# ============================================================
# app.py - StayFlow: Gestión Hotelera con Flask + SQLite
# ============================================================

from flask import Flask, render_template, request, redirect, url_for, session, flash
from database import init_db, get_db
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = 'stayflow_secret_2024'

# ============================================================
# INICIALIZACIÓN + USUARIO ADMIN POR DEFECTO
# ============================================================

_iniciado = False

@app.before_request
def setup():
    global _iniciado
    if not _iniciado:
        init_db()
        # Crear admin por defecto si no existe
        db = get_db()
        existe = db.execute('SELECT id FROM usuarios WHERE email = ?', ('admin@stayflow.com',)).fetchone()
        if not existe:
            db.execute('INSERT INTO usuarios (nombre, email, password, rol) VALUES (?,?,?,?)',
                ('Administrador', 'admin@stayflow.com', generate_password_hash('admin123'), 'admin'))
            db.commit()
        _iniciado = True

# ============================================================
# DECORADOR LOGIN
# ============================================================

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Acceso restringido. Inicia sesión.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# ============================================================
# AUTH
# ============================================================

@app.route('/')
def index():
    return redirect(url_for('dashboard') if 'user_id' in session else url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email    = request.form['email'].strip()
        password = request.form['password']
        db       = get_db()
        usuario  = db.execute('SELECT * FROM usuarios WHERE email = ?', (email,)).fetchone()
        if usuario and check_password_hash(usuario['password'], password):
            session['user_id']     = usuario['id']
            session['user_nombre'] = usuario['nombre']
            session['user_rol']    = usuario['rol']
            return redirect(url_for('dashboard'))
        flash('Credenciales incorrectas', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada correctamente', 'info')
    return redirect(url_for('login'))

# ============================================================
# DASHBOARD
# ============================================================

@app.route('/dashboard')
@login_required
def dashboard():
    db = get_db()
    total_huespedes   = db.execute('SELECT COUNT(*) as c FROM huespedes').fetchone()['c']
    total_habitaciones= db.execute('SELECT COUNT(*) as c FROM habitaciones').fetchone()['c']
    disponibles       = db.execute("SELECT COUNT(*) as c FROM habitaciones WHERE estado='disponible'").fetchone()['c']
    ocupadas          = db.execute("SELECT COUNT(*) as c FROM habitaciones WHERE estado='ocupada'").fetchone()['c']
    reservas_activas  = db.execute("SELECT COUNT(*) as c FROM reservas WHERE estado IN ('confirmada','activa')").fetchone()['c']
    ingresos          = db.execute("SELECT COALESCE(SUM(total),0) as s FROM reservas WHERE estado != 'cancelada'").fetchone()['s']

    # Próximas entradas (fecha_entrada >= hoy, ordenadas)
    proximas = db.execute('''
        SELECT r.*, h.nombre||' '||h.apellidos as huesped, hab.numero as habitacion
        FROM reservas r
        JOIN huespedes h ON h.id = r.huesped_id
        JOIN habitaciones hab ON hab.id = r.habitacion_id
        WHERE r.fecha_entrada >= DATE('now') AND r.estado IN ('confirmada','activa')
        ORDER BY r.fecha_entrada ASC LIMIT 5
    ''').fetchall()

    return render_template('dashboard.html',
        total_huespedes=total_huespedes,
        total_habitaciones=total_habitaciones,
        disponibles=disponibles, ocupadas=ocupadas,
        reservas_activas=reservas_activas, ingresos=ingresos,
        proximas=proximas)

# ============================================================
# CRUD: HUÉSPEDES
# ============================================================

@app.route('/huespedes')
@login_required
def huespedes_lista():
    q  = request.args.get('q', '').strip()
    db = get_db()
    if q:
        huespedes = db.execute(
            "SELECT * FROM huespedes WHERE nombre LIKE ? OR apellidos LIKE ? OR dni LIKE ? ORDER BY apellidos",
            (f'%{q}%', f'%{q}%', f'%{q}%')).fetchall()
    else:
        huespedes = db.execute('SELECT * FROM huespedes ORDER BY apellidos').fetchall()
    return render_template('huespedes/lista.html', huespedes=huespedes, q=q)

@app.route('/huespedes/nuevo', methods=['GET', 'POST'])
@login_required
def huespedes_nuevo():
    if request.method == 'POST':
        nombre       = request.form['nombre'].strip()
        apellidos    = request.form['apellidos'].strip()
        email        = request.form['email'].strip()
        telefono     = request.form['telefono'].strip()
        dni          = request.form['dni'].strip()
        nacionalidad = request.form['nacionalidad'].strip()
        if not nombre or not apellidos:
            flash('Nombre y apellidos son obligatorios', 'error')
        else:
            db = get_db()
            db.execute('INSERT INTO huespedes (nombre,apellidos,email,telefono,dni,nacionalidad) VALUES (?,?,?,?,?,?)',
                       (nombre, apellidos, email, telefono, dni, nacionalidad))
            db.commit()
            flash('Huésped registrado correctamente', 'success')
            return redirect(url_for('huespedes_lista'))
    return render_template('huespedes/form.html', huesped=None)

@app.route('/huespedes/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def huespedes_editar(id):
    db      = get_db()
    huesped = db.execute('SELECT * FROM huespedes WHERE id=?', (id,)).fetchone()
    if not huesped:
        flash('Huésped no encontrado', 'error')
        return redirect(url_for('huespedes_lista'))
    if request.method == 'POST':
        db.execute('''UPDATE huespedes SET nombre=?,apellidos=?,email=?,telefono=?,dni=?,nacionalidad=? WHERE id=?''',
            (request.form['nombre'].strip(), request.form['apellidos'].strip(),
             request.form['email'].strip(), request.form['telefono'].strip(),
             request.form['dni'].strip(), request.form['nacionalidad'].strip(), id))
        db.commit()
        flash('Huésped actualizado', 'success')
        return redirect(url_for('huespedes_lista'))
    return render_template('huespedes/form.html', huesped=huesped)

@app.route('/huespedes/eliminar/<int:id>', methods=['POST'])
@login_required
def huespedes_eliminar(id):
    db = get_db()
    db.execute('DELETE FROM huespedes WHERE id=?', (id,))
    db.commit()
    flash('Huésped eliminado', 'success')
    return redirect(url_for('huespedes_lista'))

# ============================================================
# CRUD: HABITACIONES
# ============================================================

@app.route('/habitaciones')
@login_required
def habitaciones_lista():
    filtro = request.args.get('estado', '')
    db     = get_db()
    if filtro:
        habs = db.execute('SELECT * FROM habitaciones WHERE estado=? ORDER BY numero', (filtro,)).fetchall()
    else:
        habs = db.execute('SELECT * FROM habitaciones ORDER BY numero').fetchall()
    return render_template('habitaciones/lista.html', habitaciones=habs, filtro=filtro)

@app.route('/habitaciones/nueva', methods=['GET', 'POST'])
@login_required
def habitaciones_nueva():
    if request.method == 'POST':
        numero       = request.form['numero'].strip()
        tipo         = request.form['tipo']
        precio_noche = request.form['precio_noche']
        capacidad    = request.form['capacidad']
        estado       = request.form['estado']
        descripcion  = request.form['descripcion'].strip()
        if not numero or not precio_noche:
            flash('Número y precio son obligatorios', 'error')
        else:
            db = get_db()
            try:
                db.execute('INSERT INTO habitaciones (numero,tipo,precio_noche,capacidad,estado,descripcion) VALUES (?,?,?,?,?,?)',
                           (numero, tipo, float(precio_noche), int(capacidad), estado, descripcion))
                db.commit()
                flash('Habitación creada', 'success')
                return redirect(url_for('habitaciones_lista'))
            except Exception:
                flash('El número de habitación ya existe', 'error')
    return render_template('habitaciones/form.html', habitacion=None)

@app.route('/habitaciones/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def habitaciones_editar(id):
    db         = get_db()
    habitacion = db.execute('SELECT * FROM habitaciones WHERE id=?', (id,)).fetchone()
    if not habitacion:
        flash('Habitación no encontrada', 'error')
        return redirect(url_for('habitaciones_lista'))
    if request.method == 'POST':
        db.execute('''UPDATE habitaciones SET numero=?,tipo=?,precio_noche=?,capacidad=?,estado=?,descripcion=? WHERE id=?''',
            (request.form['numero'].strip(), request.form['tipo'],
             float(request.form['precio_noche']), int(request.form['capacidad']),
             request.form['estado'], request.form['descripcion'].strip(), id))
        db.commit()
        flash('Habitación actualizada', 'success')
        return redirect(url_for('habitaciones_lista'))
    return render_template('habitaciones/form.html', habitacion=habitacion)

@app.route('/habitaciones/eliminar/<int:id>', methods=['POST'])
@login_required
def habitaciones_eliminar(id):
    db = get_db()
    db.execute('DELETE FROM habitaciones WHERE id=?', (id,))
    db.commit()
    flash('Habitación eliminada', 'success')
    return redirect(url_for('habitaciones_lista'))

# ============================================================
# CRUD: RESERVAS
# ============================================================

@app.route('/reservas')
@login_required
def reservas_lista():
    filtro = request.args.get('estado', '')
    db     = get_db()
    query  = '''
        SELECT r.*, h.nombre||' '||h.apellidos as huesped_nombre,
               hab.numero as hab_numero, hab.tipo as hab_tipo
        FROM reservas r
        JOIN huespedes h ON h.id = r.huesped_id
        JOIN habitaciones hab ON hab.id = r.habitacion_id
    '''
    if filtro:
        reservas = db.execute(query + ' WHERE r.estado=? ORDER BY r.fecha_entrada DESC', (filtro,)).fetchall()
    else:
        reservas = db.execute(query + ' ORDER BY r.fecha_entrada DESC').fetchall()
    return render_template('reservas/lista.html', reservas=reservas, filtro=filtro)

@app.route('/reservas/nueva', methods=['GET', 'POST'])
@login_required
def reservas_nueva():
    db = get_db()
    if request.method == 'POST':
        huesped_id    = request.form['huesped_id']
        habitacion_id = request.form['habitacion_id']
        fecha_entrada = request.form['fecha_entrada']
        fecha_salida  = request.form['fecha_salida']
        notas         = request.form['notas'].strip()
        if not huesped_id or not habitacion_id or not fecha_entrada or not fecha_salida:
            flash('Todos los campos obligatorios deben rellenarse', 'error')
        else:
            # Calcular total automáticamente
            hab    = db.execute('SELECT precio_noche FROM habitaciones WHERE id=?', (habitacion_id,)).fetchone()
            from datetime import date
            d1     = date.fromisoformat(fecha_entrada)
            d2     = date.fromisoformat(fecha_salida)
            noches = max((d2 - d1).days, 1)
            total  = noches * hab['precio_noche']
            db.execute('INSERT INTO reservas (huesped_id,habitacion_id,fecha_entrada,fecha_salida,total,notas) VALUES (?,?,?,?,?,?)',
                       (huesped_id, habitacion_id, fecha_entrada, fecha_salida, total, notas))
            db.commit()
            flash(f'Reserva creada. Total estimado: {total:.2f}€', 'success')
            return redirect(url_for('reservas_lista'))
    huespedes   = db.execute('SELECT * FROM huespedes ORDER BY apellidos').fetchall()
    habitaciones= db.execute("SELECT * FROM habitaciones WHERE estado='disponible' ORDER BY numero").fetchall()
    return render_template('reservas/form.html', reserva=None, huespedes=huespedes, habitaciones=habitaciones)

@app.route('/reservas/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def reservas_editar(id):
    db     = get_db()
    reserva= db.execute('SELECT * FROM reservas WHERE id=?', (id,)).fetchone()
    if not reserva:
        flash('Reserva no encontrada', 'error')
        return redirect(url_for('reservas_lista'))
    if request.method == 'POST':
        huesped_id    = request.form['huesped_id']
        habitacion_id = request.form['habitacion_id']
        fecha_entrada = request.form['fecha_entrada']
        fecha_salida  = request.form['fecha_salida']
        estado        = request.form['estado']
        notas         = request.form['notas'].strip()
        hab    = db.execute('SELECT precio_noche FROM habitaciones WHERE id=?', (habitacion_id,)).fetchone()
        from datetime import date
        d1     = date.fromisoformat(fecha_entrada)
        d2     = date.fromisoformat(fecha_salida)
        noches = max((d2 - d1).days, 1)
        total  = noches * hab['precio_noche']
        db.execute('''UPDATE reservas SET huesped_id=?,habitacion_id=?,fecha_entrada=?,fecha_salida=?,estado=?,total=?,notas=? WHERE id=?''',
            (huesped_id, habitacion_id, fecha_entrada, fecha_salida, estado, total, notas, id))
        db.commit()
        flash('Reserva actualizada', 'success')
        return redirect(url_for('reservas_lista'))
    huespedes   = db.execute('SELECT * FROM huespedes ORDER BY apellidos').fetchall()
    habitaciones= db.execute('SELECT * FROM habitaciones ORDER BY numero').fetchall()
    return render_template('reservas/form.html', reserva=reserva, huespedes=huespedes, habitaciones=habitaciones)

@app.route('/reservas/eliminar/<int:id>', methods=['POST'])
@login_required
def reservas_eliminar(id):
    db = get_db()
    db.execute('DELETE FROM reservas WHERE id=?', (id,))
    db.commit()
    flash('Reserva eliminada', 'success')
    return redirect(url_for('reservas_lista'))

@app.route('/reservas/detalle/<int:id>')
@login_required
def reservas_detalle(id):
    db = get_db()
    reserva = db.execute('''
        SELECT r.*, h.nombre||' '||h.apellidos as huesped_nombre, h.email as huesped_email,
               h.telefono as huesped_tel, hab.numero as hab_numero, hab.tipo as hab_tipo,
               hab.precio_noche
        FROM reservas r
        JOIN huespedes h ON h.id = r.huesped_id
        JOIN habitaciones hab ON hab.id = r.habitacion_id
        WHERE r.id=?
    ''', (id,)).fetchone()
    if not reserva:
        flash('Reserva no encontrada', 'error')
        return redirect(url_for('reservas_lista'))
    servicios = db.execute('SELECT * FROM servicios WHERE reserva_id=? ORDER BY fecha', (id,)).fetchall()
    total_servicios = sum(s['precio'] * s['cantidad'] for s in servicios)
    return render_template('reservas/detalle.html', reserva=reserva, servicios=servicios, total_servicios=total_servicios)

# ============================================================
# CRUD: SERVICIOS
# ============================================================

@app.route('/servicios/nuevo/<int:reserva_id>', methods=['POST'])
@login_required
def servicios_nuevo(reserva_id):
    nombre   = request.form['nombre'].strip()
    precio   = request.form['precio']
    cantidad = request.form.get('cantidad', 1)
    if nombre and precio:
        db = get_db()
        db.execute('INSERT INTO servicios (reserva_id,nombre,precio,cantidad) VALUES (?,?,?,?)',
                   (reserva_id, nombre, float(precio), int(cantidad)))
        db.commit()
        flash('Servicio añadido', 'success')
    return redirect(url_for('reservas_detalle', id=reserva_id))

@app.route('/servicios/eliminar/<int:id>', methods=['POST'])
@login_required
def servicios_eliminar(id):
    db       = get_db()
    servicio = db.execute('SELECT reserva_id FROM servicios WHERE id=?', (id,)).fetchone()
    if servicio:
        reserva_id = servicio['reserva_id']
        db.execute('DELETE FROM servicios WHERE id=?', (id,))
        db.commit()
        flash('Servicio eliminado', 'success')
        return redirect(url_for('reservas_detalle', id=reserva_id))
    return redirect(url_for('reservas_lista'))

# ============================================================
# CRUD: USUARIOS
# ============================================================

@app.route('/usuarios')
@login_required
def usuarios_lista():
    db       = get_db()
    usuarios = db.execute('SELECT id,nombre,email,rol,fecha_alta FROM usuarios ORDER BY nombre').fetchall()
    return render_template('usuarios/lista.html', usuarios=usuarios)

@app.route('/usuarios/nuevo', methods=['GET', 'POST'])
@login_required
def usuarios_nuevo():
    if request.method == 'POST':
        nombre   = request.form['nombre'].strip()
        email    = request.form['email'].strip()
        password = request.form['password']
        rol      = request.form['rol']
        if not nombre or not email or not password:
            flash('Todos los campos son obligatorios', 'error')
        else:
            db = get_db()
            existe = db.execute('SELECT id FROM usuarios WHERE email=?', (email,)).fetchone()
            if existe:
                flash('Ese email ya está registrado', 'error')
            else:
                db.execute('INSERT INTO usuarios (nombre,email,password,rol) VALUES (?,?,?,?)',
                           (nombre, email, generate_password_hash(password), rol))
                db.commit()
                flash('Usuario creado', 'success')
                return redirect(url_for('usuarios_lista'))
    return render_template('usuarios/form.html', usuario=None)

@app.route('/usuarios/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def usuarios_editar(id):
    db      = get_db()
    usuario = db.execute('SELECT * FROM usuarios WHERE id=?', (id,)).fetchone()
    if not usuario:
        flash('Usuario no encontrado', 'error')
        return redirect(url_for('usuarios_lista'))
    if request.method == 'POST':
        nombre = request.form['nombre'].strip()
        email  = request.form['email'].strip()
        rol    = request.form['rol']
        db.execute('UPDATE usuarios SET nombre=?,email=?,rol=? WHERE id=?', (nombre, email, rol, id))
        db.commit()
        flash('Usuario actualizado', 'success')
        return redirect(url_for('usuarios_lista'))
    return render_template('usuarios/form.html', usuario=usuario)

@app.route('/usuarios/eliminar/<int:id>', methods=['POST'])
@login_required
def usuarios_eliminar(id):
    if id == session['user_id']:
        flash('No puedes eliminarte a ti mismo', 'error')
        return redirect(url_for('usuarios_lista'))
    db = get_db()
    db.execute('DELETE FROM usuarios WHERE id=?', (id,))
    db.commit()
    flash('Usuario eliminado', 'success')
    return redirect(url_for('usuarios_lista'))

# ============================================================
# ARRANCAR
# ============================================================

if __name__ == '__main__':
    app.run(debug=True)
