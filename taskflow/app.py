# ============================================================
# TaskFlow - Aplicación SaaS de Gestión de Tareas
# Tecnología: Flask + SQLite + Jinja2
# ============================================================

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from database import init_db, get_db
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import requests
import os

app = Flask(__name__)
app.secret_key = 'taskflow_secret_2024'  # Clave para sesiones

# ============================================================
# INICIALIZACIÓN
# ============================================================

@app.before_request
def setup():
    """Inicializa la base de datos antes del primer request"""
    init_db()

# ============================================================
# DECORADOR: Proteger rutas que requieren login
# ============================================================

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Debes iniciar sesión primero', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# ============================================================
# RUTAS DE AUTENTICACIÓN
# ============================================================

@app.route('/')
def index():
    """Página de inicio - redirige según sesión"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registro de nuevos usuarios"""
    if request.method == 'POST':
        nombre = request.form['nombre'].strip()
        email = request.form['email'].strip()
        password = request.form['password']

        # Validaciones básicas
        if not nombre or not email or not password:
            flash('Todos los campos son obligatorios', 'error')
            return render_template('register.html')

        db = get_db()
        # Comprobar si el email ya existe
        usuario = db.execute('SELECT id FROM usuarios WHERE email = ?', (email,)).fetchone()
        if usuario:
            flash('Ese email ya está registrado', 'error')
            return render_template('register.html')

        # Insertar usuario con contraseña hasheada
        hashed = generate_password_hash(password)
        db.execute('INSERT INTO usuarios (nombre, email, password) VALUES (?, ?, ?)',
                   (nombre, email, hashed))
        db.commit()
        flash('Cuenta creada correctamente. ¡Inicia sesión!', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Inicio de sesión"""
    if request.method == 'POST':
        email = request.form['email'].strip()
        password = request.form['password']

        db = get_db()
        usuario = db.execute('SELECT * FROM usuarios WHERE email = ?', (email,)).fetchone()

        if usuario and check_password_hash(usuario['password'], password):
            # Guardar datos en sesión
            session['user_id'] = usuario['id']
            session['user_nombre'] = usuario['nombre']
            flash(f'Bienvenido, {usuario["nombre"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Email o contraseña incorrectos', 'error')

    return render_template('login.html')

@app.route('/logout')
def logout():
    """Cerrar sesión"""
    session.clear()
    flash('Has cerrado sesión', 'info')
    return redirect(url_for('login'))

# ============================================================
# DASHBOARD
# ============================================================

@app.route('/dashboard')
@login_required
def dashboard():
    """Panel principal con resumen de tareas"""
    db = get_db()
    user_id = session['user_id']

    # Estadísticas del usuario
    total = db.execute('SELECT COUNT(*) as c FROM tareas WHERE asignado_a = ?', (user_id,)).fetchone()['c']
    pendientes = db.execute('SELECT COUNT(*) as c FROM tareas WHERE asignado_a = ? AND estado = "pendiente"', (user_id,)).fetchone()['c']
    en_progreso = db.execute('SELECT COUNT(*) as c FROM tareas WHERE asignado_a = ? AND estado = "en_progreso"', (user_id,)).fetchone()['c']
    completadas = db.execute('SELECT COUNT(*) as c FROM tareas WHERE asignado_a = ? AND estado = "completada"', (user_id,)).fetchone()['c']

    # Últimas 5 tareas
    tareas_recientes = db.execute('''
        SELECT t.*, p.nombre as proyecto_nombre, u.nombre as asignado_nombre
        FROM tareas t
        LEFT JOIN proyectos p ON t.proyecto_id = p.id
        LEFT JOIN usuarios u ON t.asignado_a = u.id
        WHERE t.asignado_a = ?
        ORDER BY t.fecha_creacion DESC LIMIT 5
    ''', (user_id,)).fetchall()

    return render_template('dashboard.html',
                           total=total, pendientes=pendientes,
                           en_progreso=en_progreso, completadas=completadas,
                           tareas_recientes=tareas_recientes)

# ============================================================
# CRUD: USUARIOS
# ============================================================

@app.route('/usuarios')
@login_required
def usuarios_lista():
    db = get_db()
    usuarios = db.execute('SELECT id, nombre, email, fecha_registro FROM usuarios ORDER BY nombre').fetchall()
    return render_template('usuarios/lista.html', usuarios=usuarios)

@app.route('/usuarios/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def usuarios_editar(id):
    db = get_db()
    usuario = db.execute('SELECT * FROM usuarios WHERE id = ?', (id,)).fetchone()
    if not usuario:
        flash('Usuario no encontrado', 'error')
        return redirect(url_for('usuarios_lista'))

    if request.method == 'POST':
        nombre = request.form['nombre'].strip()
        email = request.form['email'].strip()
        if not nombre or not email:
            flash('Nombre y email son obligatorios', 'error')
        else:
            db.execute('UPDATE usuarios SET nombre = ?, email = ? WHERE id = ?', (nombre, email, id))
            db.commit()
            flash('Usuario actualizado', 'success')
            return redirect(url_for('usuarios_lista'))

    return render_template('usuarios/editar.html', usuario=usuario)

@app.route('/usuarios/eliminar/<int:id>', methods=['POST'])
@login_required
def usuarios_eliminar(id):
    if id == session['user_id']:
        flash('No puedes eliminarte a ti mismo', 'error')
        return redirect(url_for('usuarios_lista'))
    db = get_db()
    db.execute('DELETE FROM usuarios WHERE id = ?', (id,))
    db.commit()
    flash('Usuario eliminado', 'success')
    return redirect(url_for('usuarios_lista'))

# ============================================================
# CRUD: PROYECTOS
# ============================================================

@app.route('/proyectos')
@login_required
def proyectos_lista():
    db = get_db()
    proyectos = db.execute('''
        SELECT p.*, COUNT(t.id) as num_tareas
        FROM proyectos p
        LEFT JOIN tareas t ON t.proyecto_id = p.id
        GROUP BY p.id ORDER BY p.nombre
    ''').fetchall()
    return render_template('proyectos/lista.html', proyectos=proyectos)

@app.route('/proyectos/nuevo', methods=['GET', 'POST'])
@login_required
def proyectos_nuevo():
    if request.method == 'POST':
        nombre = request.form['nombre'].strip()
        descripcion = request.form['descripcion'].strip()
        if not nombre:
            flash('El nombre es obligatorio', 'error')
        else:
            db = get_db()
            db.execute('INSERT INTO proyectos (nombre, descripcion) VALUES (?, ?)', (nombre, descripcion))
            db.commit()
            flash('Proyecto creado', 'success')
            return redirect(url_for('proyectos_lista'))
    return render_template('proyectos/form.html', proyecto=None)

@app.route('/proyectos/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def proyectos_editar(id):
    db = get_db()
    proyecto = db.execute('SELECT * FROM proyectos WHERE id = ?', (id,)).fetchone()
    if not proyecto:
        flash('Proyecto no encontrado', 'error')
        return redirect(url_for('proyectos_lista'))

    if request.method == 'POST':
        nombre = request.form['nombre'].strip()
        descripcion = request.form['descripcion'].strip()
        if not nombre:
            flash('El nombre es obligatorio', 'error')
        else:
            db.execute('UPDATE proyectos SET nombre = ?, descripcion = ? WHERE id = ?', (nombre, descripcion, id))
            db.commit()
            flash('Proyecto actualizado', 'success')
            return redirect(url_for('proyectos_lista'))

    return render_template('proyectos/form.html', proyecto=proyecto)

@app.route('/proyectos/eliminar/<int:id>', methods=['POST'])
@login_required
def proyectos_eliminar(id):
    db = get_db()
    db.execute('DELETE FROM proyectos WHERE id = ?', (id,))
    db.commit()
    flash('Proyecto eliminado', 'success')
    return redirect(url_for('proyectos_lista'))

# ============================================================
# CRUD: TAREAS
# ============================================================

@app.route('/tareas')
@login_required
def tareas_lista():
    db = get_db()
    filtro_estado = request.args.get('estado', '')
    
    query = '''
        SELECT t.*, p.nombre as proyecto_nombre, u.nombre as asignado_nombre
        FROM tareas t
        LEFT JOIN proyectos p ON t.proyecto_id = p.id
        LEFT JOIN usuarios u ON t.asignado_a = u.id
    '''
    params = []
    if filtro_estado:
        query += ' WHERE t.estado = ?'
        params.append(filtro_estado)
    query += ' ORDER BY t.fecha_creacion DESC'

    tareas = db.execute(query, params).fetchall()
    return render_template('tareas/lista.html', tareas=tareas, filtro_estado=filtro_estado)

@app.route('/tareas/nueva', methods=['GET', 'POST'])
@login_required
def tareas_nueva():
    db = get_db()
    if request.method == 'POST':
        titulo = request.form['titulo'].strip()
        descripcion = request.form['descripcion'].strip()
        estado = request.form['estado']
        fecha_limite = request.form['fecha_limite']
        proyecto_id = request.form['proyecto_id'] or None
        asignado_a = request.form['asignado_a'] or session['user_id']

        if not titulo:
            flash('El título es obligatorio', 'error')
        else:
            db.execute('''
                INSERT INTO tareas (titulo, descripcion, estado, fecha_limite, proyecto_id, asignado_a)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (titulo, descripcion, estado, fecha_limite, proyecto_id, asignado_a))
            db.commit()
            flash('Tarea creada', 'success')
            return redirect(url_for('tareas_lista'))

    proyectos = db.execute('SELECT * FROM proyectos ORDER BY nombre').fetchall()
    usuarios = db.execute('SELECT id, nombre FROM usuarios ORDER BY nombre').fetchall()
    return render_template('tareas/form.html', tarea=None, proyectos=proyectos, usuarios=usuarios)

@app.route('/tareas/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def tareas_editar(id):
    db = get_db()
    tarea = db.execute('SELECT * FROM tareas WHERE id = ?', (id,)).fetchone()
    if not tarea:
        flash('Tarea no encontrada', 'error')
        return redirect(url_for('tareas_lista'))

    if request.method == 'POST':
        titulo = request.form['titulo'].strip()
        descripcion = request.form['descripcion'].strip()
        estado = request.form['estado']
        fecha_limite = request.form['fecha_limite']
        proyecto_id = request.form['proyecto_id'] or None
        asignado_a = request.form['asignado_a'] or session['user_id']

        if not titulo:
            flash('El título es obligatorio', 'error')
        else:
            db.execute('''
                UPDATE tareas SET titulo=?, descripcion=?, estado=?, fecha_limite=?, proyecto_id=?, asignado_a=?
                WHERE id=?
            ''', (titulo, descripcion, estado, fecha_limite, proyecto_id, asignado_a, id))
            db.commit()
            flash('Tarea actualizada', 'success')
            return redirect(url_for('tareas_lista'))

    proyectos = db.execute('SELECT * FROM proyectos ORDER BY nombre').fetchall()
    usuarios = db.execute('SELECT id, nombre FROM usuarios ORDER BY nombre').fetchall()
    return render_template('tareas/form.html', tarea=tarea, proyectos=proyectos, usuarios=usuarios)

@app.route('/tareas/eliminar/<int:id>', methods=['POST'])
@login_required
def tareas_eliminar(id):
    db = get_db()
    db.execute('DELETE FROM tareas WHERE id = ?', (id,))
    db.commit()
    flash('Tarea eliminada', 'success')
    return redirect(url_for('tareas_lista'))

@app.route('/tareas/completar/<int:id>', methods=['POST'])
@login_required
def tareas_completar(id):
    """Marcar tarea como completada (toggle)"""
    db = get_db()
    tarea = db.execute('SELECT estado FROM tareas WHERE id = ?', (id,)).fetchone()
    if tarea:
        nuevo_estado = 'pendiente' if tarea['estado'] == 'completada' else 'completada'
        db.execute('UPDATE tareas SET estado = ? WHERE id = ?', (nuevo_estado, id))
        db.commit()
    return redirect(request.referrer or url_for('tareas_lista'))

@app.route('/tareas/detalle/<int:id>')
@login_required
def tareas_detalle(id):
    db = get_db()
    tarea = db.execute('''
        SELECT t.*, p.nombre as proyecto_nombre, u.nombre as asignado_nombre
        FROM tareas t
        LEFT JOIN proyectos p ON t.proyecto_id = p.id
        LEFT JOIN usuarios u ON t.asignado_a = u.id
        WHERE t.id = ?
    ''', (id,)).fetchone()
    if not tarea:
        flash('Tarea no encontrada', 'error')
        return redirect(url_for('tareas_lista'))

    comentarios = db.execute('''
        SELECT c.*, u.nombre as autor
        FROM comentarios c
        JOIN usuarios u ON c.usuario_id = u.id
        WHERE c.tarea_id = ?
        ORDER BY c.fecha_creacion ASC
    ''', (id,)).fetchall()

    return render_template('tareas/detalle.html', tarea=tarea, comentarios=comentarios)

# ============================================================
# CRUD: COMENTARIOS
# ============================================================

@app.route('/comentarios/nuevo/<int:tarea_id>', methods=['POST'])
@login_required
def comentarios_nuevo(tarea_id):
    contenido = request.form['contenido'].strip()
    if contenido:
        db = get_db()
        db.execute('INSERT INTO comentarios (contenido, usuario_id, tarea_id) VALUES (?, ?, ?)',
                   (contenido, session['user_id'], tarea_id))
        db.commit()
        flash('Comentario añadido', 'success')
    return redirect(url_for('tareas_detalle', id=tarea_id))

@app.route('/comentarios/eliminar/<int:id>', methods=['POST'])
@login_required
def comentarios_eliminar(id):
    db = get_db()
    comentario = db.execute('SELECT * FROM comentarios WHERE id = ?', (id,)).fetchone()
    if comentario:
        tarea_id = comentario['tarea_id']
        db.execute('DELETE FROM comentarios WHERE id = ?', (id,))
        db.commit()
        flash('Comentario eliminado', 'success')
        return redirect(url_for('tareas_detalle', id=tarea_id))
    return redirect(url_for('tareas_lista'))

# ============================================================
# API: SUGERENCIA DE TÍTULO CON IA (EXTRA)
# ============================================================

@app.route('/api/sugerir-titulo', methods=['POST'])
@login_required
def sugerir_titulo():
    """Sugiere un título de tarea usando la API de Claude"""
    data = request.get_json()
    descripcion = data.get('descripcion', '')

    if not descripcion:
        return jsonify({'error': 'Falta descripción'}), 400

    try:
        respuesta = requests.post(
            'https://api.anthropic.com/v1/messages',
            headers={
                'x-api-key': os.environ.get('ANTHROPIC_API_KEY', ''),
                'anthropic-version': '2023-06-01',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'claude-haiku-4-5-20251001',
                'max_tokens': 100,
                'messages': [{
                    'role': 'user',
                    'content': f'Sugiere un título corto y claro (máximo 8 palabras) para una tarea con esta descripción: "{descripcion}". Responde SOLO con el título, sin comillas.'
                }]
            },
            timeout=10
        )
        resultado = respuesta.json()
        titulo = resultado['content'][0]['text'].strip()
        return jsonify({'titulo': titulo})
    except Exception as e:
        return jsonify({'error': 'No se pudo conectar con la IA'}), 500

# ============================================================
# ARRANCAR APLICACIÓN
# ============================================================

if __name__ == '__main__':
    app.run(debug=True)
