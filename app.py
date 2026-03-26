from flask import Flask, request, redirect, url_for, session, flash, get_flashed_messages
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)
app.secret_key = 'stayflow2024'
DB = 'stayflow.db'

# ──────────────────────────────────────────────
# BASE DE DATOS
# ──────────────────────────────────────────────

def get_db():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    db.executescript('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            rol TEXT DEFAULT 'recepcionista'
        );
        CREATE TABLE IF NOT EXISTS huespedes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            apellidos TEXT NOT NULL,
            email TEXT,
            telefono TEXT,
            dni TEXT,
            nacionalidad TEXT
        );
        CREATE TABLE IF NOT EXISTS habitaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero TEXT UNIQUE NOT NULL,
            tipo TEXT NOT NULL,
            precio_noche REAL NOT NULL,
            capacidad INTEGER DEFAULT 2,
            estado TEXT DEFAULT 'disponible',
            descripcion TEXT
        );
        CREATE TABLE IF NOT EXISTS reservas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            huesped_id INTEGER NOT NULL,
            habitacion_id INTEGER NOT NULL,
            fecha_entrada DATE NOT NULL,
            fecha_salida DATE NOT NULL,
            estado TEXT DEFAULT 'confirmada',
            total REAL DEFAULT 0,
            notas TEXT
        );
        CREATE TABLE IF NOT EXISTS servicios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reserva_id INTEGER NOT NULL,
            nombre TEXT NOT NULL,
            precio REAL NOT NULL,
            cantidad INTEGER DEFAULT 1
        );
    ''')
    # Admin por defecto
    existe = db.execute('SELECT id FROM usuarios WHERE email=?', ('admin@stayflow.com',)).fetchone()
    if not existe:
        db.execute('INSERT INTO usuarios (nombre,email,password,rol) VALUES (?,?,?,?)',
            ('Administrador', 'admin@stayflow.com', generate_password_hash('admin123'), 'admin'))
    db.commit()
    db.close()

init_db()

# ──────────────────────────────────────────────
# HELPERS HTML
# ──────────────────────────────────────────────

def flashes_html():
    msgs = get_flashed_messages(with_categories=True)
    if not msgs:
        return ''
    colors = {'success':'#d1fae5;color:#065f46', 'error':'#fee2e2;color:#991b1b',
              'info':'#dbeafe;color:#1e40af', 'warning':'#fef3c7;color:#92400e'}
    html = ''
    for cat, msg in msgs:
        c = colors.get(cat, '#f1f5f9;color:#333')
        html += f'<div style="padding:10px 16px;margin-bottom:10px;border-radius:6px;background:{c}">{msg}</div>'
    return html

CSS = '''
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: Arial, sans-serif; background: #f4f6f9; color: #333; font-size: 14px; }
a { color: #2563eb; text-decoration: none; }
.nav { background: #1e3a5f; padding: 12px 28px; display: flex; justify-content: space-between; align-items: center; }
.nav .brand { color: white; font-size: 1.1rem; font-weight: bold; }
.nav a { color: #94a3b8; margin-left: 18px; }
.nav a:hover { color: white; }
.nav .user { color: #94a3b8; font-size: 0.85rem; }
.wrap { max-width: 1050px; margin: 28px auto; padding: 0 20px; }
.hrow { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
h2 { font-size: 1.3rem; }
h3 { font-size: 1rem; margin-bottom: 14px; }
table { width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
th { background: #f8fafc; padding: 9px 13px; text-align: left; font-size: 0.75rem; text-transform: uppercase; color: #64748b; border-bottom: 1px solid #e2e8f0; }
td { padding: 9px 13px; border-bottom: 1px solid #f1f5f9; vertical-align: middle; }
tr:last-child td { border-bottom: none; }
tr:hover td { background: #f8fafc; }
.btn { display: inline-block; padding: 6px 13px; border-radius: 5px; font-size: 0.82rem; cursor: pointer; border: 1px solid transparent; text-decoration: none; }
.btn:hover { opacity: 0.85; }
.b-blue  { background: #2563eb; color: white; }
.b-green { background: #16a34a; color: white; }
.b-red   { background: #dc2626; color: white; }
.b-gray  { background: white; color: #333; border-color: #d1d5db; }
.card { background: white; padding: 28px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); max-width: 620px; }
label { display: block; font-size: 0.82rem; font-weight: bold; margin: 12px 0 4px; }
input, select, textarea { width: 100%; padding: 7px 10px; border: 1px solid #d1d5db; border-radius: 5px; font-size: 0.88rem; font-family: Arial; }
input:focus, select:focus, textarea:focus { outline: none; border-color: #2563eb; }
.row2 { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.factions { margin-top: 20px; display: flex; gap: 10px; justify-content: flex-end; border-top: 1px solid #e2e8f0; padding-top: 16px; }
.stats { display: flex; gap: 14px; margin-bottom: 22px; flex-wrap: wrap; }
.stat { background: white; padding: 14px 18px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); flex: 1; min-width: 130px; border-left: 4px solid #2563eb; }
.stat .n { font-size: 1.7rem; font-weight: bold; }
.stat .l { font-size: 0.75rem; color: #64748b; }
.badge { display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 0.72rem; font-weight: bold; }
.bd { background: #d1fae5; color: #065f46; }
.bo { background: #fee2e2; color: #991b1b; }
.bm { background: #fef3c7; color: #92400e; }
.bc { background: #dbeafe; color: #1e40af; }
.bco { background: #d1fae5; color: #065f46; }
.bcp { background: #f1f5f9; color: #475569; }
.bca { background: #fee2e2; color: #991b1b; }
.qact { display: flex; gap: 10px; margin-bottom: 22px; flex-wrap: wrap; }
.empty { text-align: center; padding: 40px; color: #64748b; background: white; border-radius: 8px; }
.login-bg { min-height: 100vh; display: flex; align-items: center; justify-content: center; background: #1e3a5f; }
.login-card { background: white; padding: 40px; border-radius: 10px; width: 100%; max-width: 380px; }
.login-card h1 { text-align: center; font-size: 1.6rem; margin-bottom: 6px; }
.login-card p { text-align: center; color: #64748b; font-size: 0.85rem; margin-bottom: 24px; }
.hint { text-align: center; margin-top: 16px; font-size: 0.8rem; color: #64748b; }
.detblock { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 18px; }
.detmeta { display: flex; flex-wrap: wrap; gap: 14px; font-size: 0.85rem; color: #64748b; background: #f8fafc; padding: 12px; border-radius: 6px; margin: 12px 0; }
.totalbox { display: flex; justify-content: space-between; padding: 10px 14px; background: #f8fafc; border-radius: 6px; margin-top: 10px; border: 1px solid #e2e8f0; }
.totalbox.dark { background: #1e3a5f; color: white; border-color: #1e3a5f; }
.filters { display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; }
.section { margin-top: 26px; }
</style>
'''

def nav():
    nombre = session.get('user_nombre', '')
    return f'''
    <nav class="nav">
        <span class="brand">🏨 StayFlow</span>
        <div>
            <a href="/dashboard">Dashboard</a>
            <a href="/reservas">Reservas</a>
            <a href="/habitaciones">Habitaciones</a>
            <a href="/huespedes">Huéspedes</a>
            <a href="/usuarios">Usuarios</a>
        </div>
        <span class="user">👤 {nombre} &nbsp; <a href="/logout" style="color:#f87171">Salir</a></span>
    </nav>'''

def page(body):
    return CSS + nav() + f'<div class="wrap">{flashes_html()}{body}</div>'

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Inicia sesión primero', 'error')
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated

def badge(estado):
    clases = {'disponible':'bd','ocupada':'bo','mantenimiento':'bm',
              'confirmada':'bc','activa':'bco','completada':'bcp','cancelada':'bca'}
    c = clases.get(estado, 'bc')
    return f'<span class="badge {c}">{estado}</span>'

# ──────────────────────────────────────────────
# AUTH
# ──────────────────────────────────────────────

@app.route('/')
def index():
    return redirect('/dashboard' if 'user_id' in session else '/login')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        db = get_db()
        u = db.execute('SELECT * FROM usuarios WHERE email=?', (request.form['email'].strip(),)).fetchone()
        db.close()
        if u and check_password_hash(u['password'], request.form['password']):
            session['user_id'] = u['id']
            session['user_nombre'] = u['nombre']
            return redirect('/dashboard')
        flash('Email o contraseña incorrectos', 'error')

    msgs = flashes_html()
    return CSS + f'''
    <div class="login-bg">
      <div class="login-card">
        <h1>🏨 StayFlow</h1>
        <p>Panel de gestión hotelera</p>
        {msgs}
        <form method="POST">
          <label>Email</label>
          <input type="email" name="email" required placeholder="admin@stayflow.com">
          <label>Contraseña</label>
          <input type="password" name="password" required placeholder="••••••••">
          <br><br>
          <button type="submit" class="btn b-blue" style="width:100%;padding:10px">Iniciar sesión</button>
        </form>
        <p class="hint">Por defecto: admin@stayflow.com / admin123</p>
      </div>
    </div>'''

@app.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada', 'info')
    return redirect('/login')

# ──────────────────────────────────────────────
# DASHBOARD
# ──────────────────────────────────────────────

@app.route('/dashboard')
@login_required
def dashboard():
    db = get_db()
    th = db.execute('SELECT COUNT(*) as c FROM huespedes').fetchone()['c']
    td = db.execute("SELECT COUNT(*) as c FROM habitaciones WHERE estado='disponible'").fetchone()['c']
    to = db.execute("SELECT COUNT(*) as c FROM habitaciones WHERE estado='ocupada'").fetchone()['c']
    tr = db.execute("SELECT COUNT(*) as c FROM reservas WHERE estado IN ('confirmada','activa')").fetchone()['c']
    ti = db.execute("SELECT COALESCE(SUM(total),0) as s FROM reservas WHERE estado!='cancelada'").fetchone()['s']
    proximas = db.execute('''
        SELECT r.id, r.fecha_entrada, r.estado,
               h.nombre||' '||h.apellidos as huesped, hab.numero as habitacion
        FROM reservas r
        JOIN huespedes h ON h.id=r.huesped_id
        JOIN habitaciones hab ON hab.id=r.habitacion_id
        WHERE r.fecha_entrada >= DATE('now') AND r.estado IN ('confirmada','activa')
        ORDER BY r.fecha_entrada ASC LIMIT 6
    ''').fetchall()
    db.close()

    filas = ''.join(f'''<tr>
        <td>{r["fecha_entrada"]}</td><td>{r["huesped"]}</td>
        <td>Hab. {r["habitacion"]}</td><td>{badge(r["estado"])}</td>
        <td><a href="/reservas/{r["id"]}" class="btn b-gray">Ver</a></td>
    </tr>''' for r in proximas)

    tabla = f'''<table><thead><tr><th>Entrada</th><th>Huésped</th><th>Hab.</th><th>Estado</th><th></th></tr></thead>
    <tbody>{filas}</tbody></table>''' if proximas else '<p style="color:#64748b">No hay próximas entradas.</p>'

    body = f'''
    <div class="hrow"><h2>Dashboard</h2></div>
    <div class="stats">
      <div class="stat" style="border-color:#2563eb"><div class="n">{tr}</div><div class="l">Reservas activas</div></div>
      <div class="stat" style="border-color:#16a34a"><div class="n">{td}</div><div class="l">Hab. disponibles</div></div>
      <div class="stat" style="border-color:#dc2626"><div class="n">{to}</div><div class="l">Hab. ocupadas</div></div>
      <div class="stat" style="border-color:#d97706"><div class="n">{th}</div><div class="l">Huéspedes</div></div>
      <div class="stat" style="border-color:#7c3aed"><div class="n">{ti:.0f}€</div><div class="l">Ingresos</div></div>
    </div>
    <div class="qact">
      <a href="/reservas/nueva" class="btn b-blue">+ Nueva reserva</a>
      <a href="/huespedes/nuevo" class="btn b-green">+ Nuevo huésped</a>
      <a href="/habitaciones/nueva" class="btn b-gray">+ Nueva habitación</a>
    </div>
    <div class="section"><h3>Próximas entradas</h3>{tabla}</div>'''
    return page(body)

# ──────────────────────────────────────────────
# HUÉSPEDES
# ──────────────────────────────────────────────

@app.route('/huespedes')
@login_required
def huespedes_lista():
    db = get_db()
    q = request.args.get('q','').strip()
    if q:
        rows = db.execute("SELECT * FROM huespedes WHERE nombre LIKE ? OR apellidos LIKE ? OR dni LIKE ? ORDER BY apellidos",
                          (f'%{q}%',f'%{q}%',f'%{q}%')).fetchall()
    else:
        rows = db.execute('SELECT * FROM huespedes ORDER BY apellidos').fetchall()
    db.close()
    filas = ''.join(f'''<tr><td>{r["id"]}</td><td><b>{r["apellidos"]}, {r["nombre"]}</b></td>
        <td>{r["dni"] or "—"}</td><td>{r["email"] or "—"}</td><td>{r["telefono"] or "—"}</td><td>{r["nacionalidad"] or "—"}</td>
        <td>
          <a href="/huespedes/{r["id"]}/editar" class="btn b-gray">✏️</a>
          <form method="POST" action="/huespedes/{r["id"]}/eliminar" style="display:inline"
                onsubmit="return confirm('¿Eliminar?')">
            <button class="btn b-red">🗑</button>
          </form>
        </td></tr>''' for r in rows)
    tabla = f'<table><thead><tr><th>#</th><th>Nombre</th><th>DNI</th><th>Email</th><th>Tel.</th><th>País</th><th></th></tr></thead><tbody>{filas}</tbody></table>' if rows else '<div class="empty"><p>No hay huéspedes.</p></div>'
    body = f'''
    <div class="hrow"><h2>Huéspedes</h2><a href="/huespedes/nuevo" class="btn b-blue">+ Nuevo huésped</a></div>
    <form method="GET" style="margin-bottom:14px;display:flex;gap:8px">
      <input type="text" name="q" value="{q}" placeholder="Buscar..." style="width:280px">
      <button type="submit" class="btn b-gray">Buscar</button>
      {"<a href='/huespedes' class='btn b-gray'>✕</a>" if q else ""}
    </form>
    {tabla}'''
    return page(body)

@app.route('/huespedes/nuevo', methods=['GET','POST'])
@login_required
def huespedes_nuevo():
    if request.method == 'POST':
        db = get_db()
        db.execute('INSERT INTO huespedes (nombre,apellidos,email,telefono,dni,nacionalidad) VALUES (?,?,?,?,?,?)',
            (request.form['nombre'], request.form['apellidos'], request.form['email'],
             request.form['telefono'], request.form['dni'], request.form['nacionalidad']))
        db.commit(); db.close()
        flash('Huésped registrado', 'success')
        return redirect('/huespedes')
    body = '''
    <div class="hrow"><h2>Nuevo huésped</h2><a href="/huespedes" class="btn b-gray">← Volver</a></div>
    <div class="card"><form method="POST">
      <div class="row2">
        <div><label>Nombre *</label><input name="nombre" required></div>
        <div><label>Apellidos *</label><input name="apellidos" required></div>
      </div>
      <div class="row2">
        <div><label>DNI/Pasaporte</label><input name="dni"></div>
        <div><label>Nacionalidad</label><input name="nacionalidad"></div>
      </div>
      <div class="row2">
        <div><label>Email</label><input type="email" name="email"></div>
        <div><label>Teléfono</label><input name="telefono"></div>
      </div>
      <div class="factions">
        <a href="/huespedes" class="btn b-gray">Cancelar</a>
        <button type="submit" class="btn b-blue">Registrar huésped</button>
      </div>
    </form></div>'''
    return page(body)

@app.route('/huespedes/<int:id>/editar', methods=['GET','POST'])
@login_required
def huespedes_editar(id):
    db = get_db()
    h = db.execute('SELECT * FROM huespedes WHERE id=?', (id,)).fetchone()
    if request.method == 'POST':
        db.execute('UPDATE huespedes SET nombre=?,apellidos=?,email=?,telefono=?,dni=?,nacionalidad=? WHERE id=?',
            (request.form['nombre'], request.form['apellidos'], request.form['email'],
             request.form['telefono'], request.form['dni'], request.form['nacionalidad'], id))
        db.commit(); db.close()
        flash('Huésped actualizado', 'success')
        return redirect('/huespedes')
    body = f'''
    <div class="hrow"><h2>Editar huésped</h2><a href="/huespedes" class="btn b-gray">← Volver</a></div>
    <div class="card"><form method="POST">
      <div class="row2">
        <div><label>Nombre *</label><input name="nombre" required value="{h["nombre"]}"></div>
        <div><label>Apellidos *</label><input name="apellidos" required value="{h["apellidos"]}"></div>
      </div>
      <div class="row2">
        <div><label>DNI/Pasaporte</label><input name="dni" value="{h["dni"] or ""}"></div>
        <div><label>Nacionalidad</label><input name="nacionalidad" value="{h["nacionalidad"] or ""}"></div>
      </div>
      <div class="row2">
        <div><label>Email</label><input type="email" name="email" value="{h["email"] or ""}"></div>
        <div><label>Teléfono</label><input name="telefono" value="{h["telefono"] or ""}"></div>
      </div>
      <div class="factions">
        <a href="/huespedes" class="btn b-gray">Cancelar</a>
        <button type="submit" class="btn b-blue">Guardar cambios</button>
      </div>
    </form></div>'''
    return page(body)

@app.route('/huespedes/<int:id>/eliminar', methods=['POST'])
@login_required
def huespedes_eliminar(id):
    db = get_db()
    db.execute('DELETE FROM huespedes WHERE id=?', (id,))
    db.commit(); db.close()
    flash('Huésped eliminado', 'success')
    return redirect('/huespedes')

# ──────────────────────────────────────────────
# HABITACIONES
# ──────────────────────────────────────────────

@app.route('/habitaciones')
@login_required
def habitaciones_lista():
    filtro = request.args.get('estado','')
    db = get_db()
    if filtro:
        rows = db.execute('SELECT * FROM habitaciones WHERE estado=? ORDER BY numero', (filtro,)).fetchall()
    else:
        rows = db.execute('SELECT * FROM habitaciones ORDER BY numero').fetchall()
    db.close()
    filas = ''.join(f'''<tr>
        <td><b>{r["numero"]}</b></td><td>{r["tipo"].capitalize()}</td>
        <td>{r["capacidad"]} pers.</td><td>{r["precio_noche"]:.2f}€</td>
        <td>{badge(r["estado"])}</td><td style="color:#64748b">{r["descripcion"] or "—"}</td>
        <td>
          <a href="/habitaciones/{r["id"]}/editar" class="btn b-gray">✏️</a>
          <form method="POST" action="/habitaciones/{r["id"]}/eliminar" style="display:inline"
                onsubmit="return confirm('¿Eliminar?')">
            <button class="btn b-red">🗑</button>
          </form>
        </td></tr>''' for r in rows)
    tabla = f'<table><thead><tr><th>Nº</th><th>Tipo</th><th>Cap.</th><th>Precio</th><th>Estado</th><th>Desc.</th><th></th></tr></thead><tbody>{filas}</tbody></table>' if rows else '<div class="empty"><p>No hay habitaciones.</p></div>'

    def fb(e, txt):
        active = 'b-blue' if filtro == e or (e == '' and not filtro) else 'b-gray'
        return f'<a href="/habitaciones{"?estado="+e if e else ""}" class="btn {active}">{txt}</a>'

    body = f'''
    <div class="hrow"><h2>Habitaciones</h2><a href="/habitaciones/nueva" class="btn b-blue">+ Nueva</a></div>
    <div class="filters">
      {fb("","Todas")}{fb("disponible","Disponibles")}{fb("ocupada","Ocupadas")}{fb("mantenimiento","Mantenimiento")}
    </div>{tabla}'''
    return page(body)

@app.route('/habitaciones/nueva', methods=['GET','POST'])
@login_required
def habitaciones_nueva():
    if request.method == 'POST':
        db = get_db()
        try:
            db.execute('INSERT INTO habitaciones (numero,tipo,precio_noche,capacidad,estado,descripcion) VALUES (?,?,?,?,?,?)',
                (request.form['numero'], request.form['tipo'], float(request.form['precio_noche']),
                 int(request.form['capacidad']), request.form['estado'], request.form['descripcion']))
            db.commit()
            flash('Habitación creada', 'success')
            return redirect('/habitaciones')
        except:
            flash('El número de habitación ya existe', 'error')
        db.close()
    body = '''
    <div class="hrow"><h2>Nueva habitación</h2><a href="/habitaciones" class="btn b-gray">← Volver</a></div>
    <div class="card"><form method="POST">
      <div class="row2">
        <div><label>Número *</label><input name="numero" required placeholder="101"></div>
        <div><label>Tipo *</label>
          <select name="tipo"><option value="individual">Individual</option><option value="doble">Doble</option><option value="suite">Suite</option></select>
        </div>
      </div>
      <div class="row2">
        <div><label>Precio/noche (€) *</label><input type="number" name="precio_noche" required step="0.01" min="0"></div>
        <div><label>Capacidad</label><input type="number" name="capacidad" value="2" min="1" max="10"></div>
      </div>
      <div><label>Estado</label>
        <select name="estado"><option value="disponible">Disponible</option><option value="ocupada">Ocupada</option><option value="mantenimiento">Mantenimiento</option></select>
      </div>
      <div><label>Descripción</label><textarea name="descripcion" rows="2"></textarea></div>
      <div class="factions">
        <a href="/habitaciones" class="btn b-gray">Cancelar</a>
        <button type="submit" class="btn b-blue">Crear habitación</button>
      </div>
    </form></div>'''
    return page(body)

@app.route('/habitaciones/<int:id>/editar', methods=['GET','POST'])
@login_required
def habitaciones_editar(id):
    db = get_db()
    h = db.execute('SELECT * FROM habitaciones WHERE id=?', (id,)).fetchone()
    if request.method == 'POST':
        db.execute('UPDATE habitaciones SET numero=?,tipo=?,precio_noche=?,capacidad=?,estado=?,descripcion=? WHERE id=?',
            (request.form['numero'], request.form['tipo'], float(request.form['precio_noche']),
             int(request.form['capacidad']), request.form['estado'], request.form['descripcion'], id))
        db.commit(); db.close()
        flash('Habitación actualizada', 'success')
        return redirect('/habitaciones')

    def sel(campo, val):
        return 'selected' if h[campo] == val else ''

    body = f'''
    <div class="hrow"><h2>Editar habitación</h2><a href="/habitaciones" class="btn b-gray">← Volver</a></div>
    <div class="card"><form method="POST">
      <div class="row2">
        <div><label>Número *</label><input name="numero" required value="{h["numero"]}"></div>
        <div><label>Tipo *</label>
          <select name="tipo">
            <option value="individual" {sel("tipo","individual")}>Individual</option>
            <option value="doble" {sel("tipo","doble")}>Doble</option>
            <option value="suite" {sel("tipo","suite")}>Suite</option>
          </select>
        </div>
      </div>
      <div class="row2">
        <div><label>Precio/noche (€) *</label><input type="number" name="precio_noche" required step="0.01" value="{h["precio_noche"]}"></div>
        <div><label>Capacidad</label><input type="number" name="capacidad" value="{h["capacidad"]}" min="1"></div>
      </div>
      <div><label>Estado</label>
        <select name="estado">
          <option value="disponible" {sel("estado","disponible")}>Disponible</option>
          <option value="ocupada" {sel("estado","ocupada")}>Ocupada</option>
          <option value="mantenimiento" {sel("estado","mantenimiento")}>Mantenimiento</option>
        </select>
      </div>
      <div><label>Descripción</label><textarea name="descripcion" rows="2">{h["descripcion"] or ""}</textarea></div>
      <div class="factions">
        <a href="/habitaciones" class="btn b-gray">Cancelar</a>
        <button type="submit" class="btn b-blue">Guardar cambios</button>
      </div>
    </form></div>'''
    return page(body)

@app.route('/habitaciones/<int:id>/eliminar', methods=['POST'])
@login_required
def habitaciones_eliminar(id):
    db = get_db()
    db.execute('DELETE FROM habitaciones WHERE id=?', (id,))
    db.commit(); db.close()
    flash('Habitación eliminada', 'success')
    return redirect('/habitaciones')

# ──────────────────────────────────────────────
# RESERVAS
# ──────────────────────────────────────────────

@app.route('/reservas')
@login_required
def reservas_lista():
    filtro = request.args.get('estado','')
    db = get_db()
    q = '''SELECT r.*, h.nombre||" "||h.apellidos as huesped_nombre,
           hab.numero as hab_numero, hab.tipo as hab_tipo
           FROM reservas r
           JOIN huespedes h ON h.id=r.huesped_id
           JOIN habitaciones hab ON hab.id=r.habitacion_id'''
    rows = db.execute(q + (' WHERE r.estado=? ORDER BY r.fecha_entrada DESC' if filtro else ' ORDER BY r.fecha_entrada DESC'),
                      (filtro,) if filtro else ()).fetchall()
    db.close()
    filas = ''.join(f'''<tr>
        <td>{r["id"]}</td><td>{r["huesped_nombre"]}</td>
        <td>{r["hab_numero"]} <small style="color:#94a3b8">({r["hab_tipo"]})</small></td>
        <td>{r["fecha_entrada"]}</td><td>{r["fecha_salida"]}</td>
        <td><b>{r["total"]:.2f}€</b></td><td>{badge(r["estado"])}</td>
        <td>
          <a href="/reservas/{r["id"]}" class="btn b-gray">Ver</a>
          <a href="/reservas/{r["id"]}/editar" class="btn b-gray">✏️</a>
          <form method="POST" action="/reservas/{r["id"]}/eliminar" style="display:inline"
                onsubmit="return confirm('¿Eliminar?')">
            <button class="btn b-red">🗑</button>
          </form>
        </td></tr>''' for r in rows)
    tabla = f'<table><thead><tr><th>#</th><th>Huésped</th><th>Hab.</th><th>Entrada</th><th>Salida</th><th>Total</th><th>Estado</th><th></th></tr></thead><tbody>{filas}</tbody></table>' if rows else '<div class="empty"><p>No hay reservas.</p></div>'

    def fb(e, txt):
        active = 'b-blue' if filtro == e or (e == '' and not filtro) else 'b-gray'
        return f'<a href="/reservas{"?estado="+e if e else ""}" class="btn {active}">{txt}</a>'

    body = f'''
    <div class="hrow"><h2>Reservas</h2><a href="/reservas/nueva" class="btn b-blue">+ Nueva reserva</a></div>
    <div class="filters">
      {fb("","Todas")}{fb("confirmada","Confirmadas")}{fb("activa","Activas")}{fb("completada","Completadas")}{fb("cancelada","Canceladas")}
    </div>{tabla}'''
    return page(body)

@app.route('/reservas/nueva', methods=['GET','POST'])
@login_required
def reservas_nueva():
    db = get_db()
    if request.method == 'POST':
        from datetime import date
        hid = request.form['huesped_id']
        habid = request.form['habitacion_id']
        fe = request.form['fecha_entrada']
        fs = request.form['fecha_salida']
        notas = request.form.get('notas','')
        hab = db.execute('SELECT precio_noche FROM habitaciones WHERE id=?', (habid,)).fetchone()
        noches = max((date.fromisoformat(fs) - date.fromisoformat(fe)).days, 1)
        total = noches * hab['precio_noche']
        db.execute('INSERT INTO reservas (huesped_id,habitacion_id,fecha_entrada,fecha_salida,total,notas) VALUES (?,?,?,?,?,?)',
                   (hid, habid, fe, fs, total, notas))
        db.commit(); db.close()
        flash(f'Reserva creada. Total: {total:.2f}€', 'success')
        return redirect('/reservas')
    huespedes = db.execute('SELECT * FROM huespedes ORDER BY apellidos').fetchall()
    habitaciones = db.execute("SELECT * FROM habitaciones WHERE estado='disponible' ORDER BY numero").fetchall()
    db.close()
    opts_h = ''.join(f'<option value="{h["id"]}">{h["apellidos"]}, {h["nombre"]}</option>' for h in huespedes)
    opts_hab = ''.join(f'<option value="{h["id"]}">Hab. {h["numero"]} - {h["tipo"].capitalize()} ({h["precio_noche"]:.2f}€/noche)</option>' for h in habitaciones)
    body = f'''
    <div class="hrow"><h2>Nueva reserva</h2><a href="/reservas" class="btn b-gray">← Volver</a></div>
    <div class="card"><form method="POST">
      <div class="row2">
        <div><label>Huésped *</label><select name="huesped_id" required><option value="">— Selecciona —</option>{opts_h}</select></div>
        <div><label>Habitación *</label><select name="habitacion_id" required><option value="">— Selecciona —</option>{opts_hab}</select></div>
      </div>
      <div class="row2">
        <div><label>Fecha entrada *</label><input type="date" name="fecha_entrada" required></div>
        <div><label>Fecha salida *</label><input type="date" name="fecha_salida" required></div>
      </div>
      <div><label>Notas</label><textarea name="notas" rows="2" placeholder="Peticiones especiales..."></textarea></div>
      <p style="color:#64748b;font-size:0.8rem;margin-top:8px">💡 El total se calcula automáticamente.</p>
      <div class="factions">
        <a href="/reservas" class="btn b-gray">Cancelar</a>
        <button type="submit" class="btn b-blue">Crear reserva</button>
      </div>
    </form></div>'''
    return page(body)

@app.route('/reservas/<int:id>/editar', methods=['GET','POST'])
@login_required
def reservas_editar(id):
    db = get_db()
    r = db.execute('SELECT * FROM reservas WHERE id=?', (id,)).fetchone()
    if request.method == 'POST':
        from datetime import date
        habid = request.form['habitacion_id']
        fe = request.form['fecha_entrada']
        fs = request.form['fecha_salida']
        hab = db.execute('SELECT precio_noche FROM habitaciones WHERE id=?', (habid,)).fetchone()
        noches = max((date.fromisoformat(fs) - date.fromisoformat(fe)).days, 1)
        total = noches * hab['precio_noche']
        db.execute('UPDATE reservas SET huesped_id=?,habitacion_id=?,fecha_entrada=?,fecha_salida=?,estado=?,total=?,notas=? WHERE id=?',
            (request.form['huesped_id'], habid, fe, fs, request.form['estado'], total, request.form.get('notas',''), id))
        db.commit(); db.close()
        flash('Reserva actualizada', 'success')
        return redirect('/reservas')
    huespedes = db.execute('SELECT * FROM huespedes ORDER BY apellidos').fetchall()
    habitaciones = db.execute('SELECT * FROM habitaciones ORDER BY numero').fetchall()
    db.close()

    def selh(hid):
        return 'selected' if r['huesped_id'] == hid else ''
    def selhab(hid):
        return 'selected' if r['habitacion_id'] == hid else ''
    def sele(e):
        return 'selected' if r['estado'] == e else ''

    opts_h = ''.join(f'<option value="{h["id"]}" {selh(h["id"])}>{h["apellidos"]}, {h["nombre"]}</option>' for h in huespedes)
    opts_hab = ''.join(f'<option value="{h["id"]}" {selhab(h["id"])}>Hab. {h["numero"]} - {h["tipo"].capitalize()} ({h["precio_noche"]:.2f}€/noche)</option>' for h in habitaciones)
    body = f'''
    <div class="hrow"><h2>Editar reserva</h2><a href="/reservas" class="btn b-gray">← Volver</a></div>
    <div class="card"><form method="POST">
      <div class="row2">
        <div><label>Huésped *</label><select name="huesped_id" required>{opts_h}</select></div>
        <div><label>Habitación *</label><select name="habitacion_id" required>{opts_hab}</select></div>
      </div>
      <div class="row2">
        <div><label>Fecha entrada *</label><input type="date" name="fecha_entrada" required value="{r["fecha_entrada"]}"></div>
        <div><label>Fecha salida *</label><input type="date" name="fecha_salida" required value="{r["fecha_salida"]}"></div>
      </div>
      <div><label>Estado</label>
        <select name="estado">
          <option value="confirmada" {sele("confirmada")}>Confirmada</option>
          <option value="activa" {sele("activa")}>Activa</option>
          <option value="completada" {sele("completada")}>Completada</option>
          <option value="cancelada" {sele("cancelada")}>Cancelada</option>
        </select>
      </div>
      <div><label>Notas</label><textarea name="notas" rows="2">{r["notas"] or ""}</textarea></div>
      <div class="factions">
        <a href="/reservas" class="btn b-gray">Cancelar</a>
        <button type="submit" class="btn b-blue">Guardar cambios</button>
      </div>
    </form></div>'''
    return page(body)

@app.route('/reservas/<int:id>/eliminar', methods=['POST'])
@login_required
def reservas_eliminar(id):
    db = get_db()
    db.execute('DELETE FROM reservas WHERE id=?', (id,))
    db.commit(); db.close()
    flash('Reserva eliminada', 'success')
    return redirect('/reservas')

@app.route('/reservas/<int:id>')
@login_required
def reservas_detalle(id):
    db = get_db()
    r = db.execute('''SELECT r.*, h.nombre||" "||h.apellidos as huesped_nombre,
        h.email as huesped_email, h.telefono as huesped_tel,
        hab.numero as hab_numero, hab.tipo as hab_tipo, hab.precio_noche
        FROM reservas r
        JOIN huespedes h ON h.id=r.huesped_id
        JOIN habitaciones hab ON hab.id=r.habitacion_id
        WHERE r.id=?''', (id,)).fetchone()
    servicios = db.execute('SELECT * FROM servicios WHERE reserva_id=?', (id,)).fetchall()
    db.close()
    total_s = sum(s['precio'] * s['cantidad'] for s in servicios)
    filas_s = ''.join(f'''<tr><td>{s["nombre"]}</td><td>{s["precio"]:.2f}€</td><td>{s["cantidad"]}</td>
        <td><b>{s["precio"]*s["cantidad"]:.2f}€</b></td>
        <td><form method="POST" action="/servicios/{s["id"]}/eliminar" style="display:inline"
              onsubmit="return confirm('¿Eliminar?')">
          <button class="btn b-red">🗑</button></form></td></tr>''' for s in servicios)
    tabla_s = f'<table><thead><tr><th>Servicio</th><th>Precio</th><th>Cant.</th><th>Subtotal</th><th></th></tr></thead><tbody>{filas_s}</tbody></table>' if servicios else '<p style="color:#64748b;margin-bottom:14px">Sin servicios extra.</p>'

    body = f'''
    <div class="hrow">
      <h2>Reserva #{r["id"]}</h2>
      <div><a href="/reservas/{r["id"]}/editar" class="btn b-gray">✏️ Editar</a> <a href="/reservas" class="btn b-gray">← Volver</a></div>
    </div>
    <div class="detblock">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
        <h3 style="margin:0">{r["huesped_nombre"]}</h3>
        {badge(r["estado"])}
      </div>
      <div class="detmeta">
        <span>🛏 Hab. {r["hab_numero"]} — {r["hab_tipo"].capitalize()}</span>
        <span>📅 Entrada: <b>{r["fecha_entrada"]}</b></span>
        <span>📅 Salida: <b>{r["fecha_salida"]}</b></span>
        <span>💶 {r["precio_noche"]:.2f}€/noche</span>
        <span>📧 {r["huesped_email"] or "—"}</span>
        <span>📞 {r["huesped_tel"] or "—"}</span>
      </div>
      {"<p><b>Notas:</b> "+r["notas"]+"</p>" if r["notas"] else ""}
      <div class="totalbox"><span>Total habitación</span><b>{r["total"]:.2f}€</b></div>
    </div>
    <div class="section">
      <h3>Servicios extra</h3>
      {tabla_s}
      {"<div class='totalbox'><span>Total servicios</span><b>"+f"{total_s:.2f}€</b></div>" if servicios else ""}
      {"<div class='totalbox dark'><span>TOTAL GENERAL</span><b>"+f"{r['total']+total_s:.2f}€</b></div>" if servicios else ""}
      <div class="detblock" style="margin-top:18px">
        <h3>Añadir servicio</h3>
        <form method="POST" action="/servicios/nuevo/{r["id"]}">
          <div class="row2">
            <div><label>Nombre</label><input name="nombre" required placeholder="Minibar, Spa..."></div>
            <div><label>Precio (€)</label><input type="number" name="precio" required step="0.01" min="0"></div>
          </div>
          <div style="max-width:200px"><label>Cantidad</label><input type="number" name="cantidad" value="1" min="1"></div>
          <div class="factions"><button type="submit" class="btn b-blue">Añadir servicio</button></div>
        </form>
      </div>
    </div>'''
    return page(body)

# ──────────────────────────────────────────────
# SERVICIOS
# ──────────────────────────────────────────────

@app.route('/servicios/nuevo/<int:reserva_id>', methods=['POST'])
@login_required
def servicios_nuevo(reserva_id):
    db = get_db()
    db.execute('INSERT INTO servicios (reserva_id,nombre,precio,cantidad) VALUES (?,?,?,?)',
        (reserva_id, request.form['nombre'], float(request.form['precio']), int(request.form.get('cantidad',1))))
    db.commit(); db.close()
    flash('Servicio añadido', 'success')
    return redirect(f'/reservas/{reserva_id}')

@app.route('/servicios/<int:id>/eliminar', methods=['POST'])
@login_required
def servicios_eliminar(id):
    db = get_db()
    s = db.execute('SELECT reserva_id FROM servicios WHERE id=?', (id,)).fetchone()
    rid = s['reserva_id']
    db.execute('DELETE FROM servicios WHERE id=?', (id,))
    db.commit(); db.close()
    flash('Servicio eliminado', 'success')
    return redirect(f'/reservas/{rid}')

# ──────────────────────────────────────────────
# USUARIOS
# ──────────────────────────────────────────────

@app.route('/usuarios')
@login_required
def usuarios_lista():
    db = get_db()
    rows = db.execute('SELECT id,nombre,email,rol FROM usuarios ORDER BY nombre').fetchall()
    db.close()
    filas = ''.join(f'''<tr><td>{r["id"]}</td><td>{r["nombre"]}{"&nbsp;<small style='background:#2563eb;color:white;padding:1px 6px;border-radius:999px;font-size:0.7rem'>Tú</small>" if r["id"]==session["user_id"] else ""}</td>
        <td>{r["email"]}</td><td>{r["rol"]}</td>
        <td>
          <a href="/usuarios/{r["id"]}/editar" class="btn b-gray">✏️</a>
          {"" if r["id"]==session["user_id"] else f'<form method="POST" action="/usuarios/{r["id"]}/eliminar" style="display:inline" onsubmit="return confirm(chr(191)+\'Eliminar?\')"><button class="btn b-red">🗑</button></form>'}
        </td></tr>''' for r in rows)
    body = f'''
    <div class="hrow"><h2>Usuarios</h2><a href="/usuarios/nuevo" class="btn b-blue">+ Nuevo usuario</a></div>
    <table><thead><tr><th>#</th><th>Nombre</th><th>Email</th><th>Rol</th><th></th></tr></thead>
    <tbody>{filas}</tbody></table>'''
    return page(body)

@app.route('/usuarios/nuevo', methods=['GET','POST'])
@login_required
def usuarios_nuevo():
    if request.method == 'POST':
        db = get_db()
        existe = db.execute('SELECT id FROM usuarios WHERE email=?', (request.form['email'],)).fetchone()
        if existe:
            flash('Ese email ya existe', 'error')
        else:
            db.execute('INSERT INTO usuarios (nombre,email,password,rol) VALUES (?,?,?,?)',
                (request.form['nombre'], request.form['email'],
                 generate_password_hash(request.form['password']), request.form['rol']))
            db.commit()
            flash('Usuario creado', 'success')
            return redirect('/usuarios')
        db.close()
    body = '''
    <div class="hrow"><h2>Nuevo usuario</h2><a href="/usuarios" class="btn b-gray">← Volver</a></div>
    <div class="card"><form method="POST">
      <label>Nombre *</label><input name="nombre" required>
      <label>Email *</label><input type="email" name="email" required>
      <label>Contraseña *</label><input type="password" name="password" required minlength="6">
      <label>Rol</label>
      <select name="rol"><option value="recepcionista">Recepcionista</option><option value="admin">Administrador</option></select>
      <div class="factions">
        <a href="/usuarios" class="btn b-gray">Cancelar</a>
        <button type="submit" class="btn b-blue">Crear usuario</button>
      </div>
    </form></div>'''
    return page(body)

@app.route('/usuarios/<int:id>/editar', methods=['GET','POST'])
@login_required
def usuarios_editar(id):
    db = get_db()
    u = db.execute('SELECT * FROM usuarios WHERE id=?', (id,)).fetchone()
    if request.method == 'POST':
        db.execute('UPDATE usuarios SET nombre=?,email=?,rol=? WHERE id=?',
            (request.form['nombre'], request.form['email'], request.form['rol'], id))
        db.commit(); db.close()
        flash('Usuario actualizado', 'success')
        return redirect('/usuarios')
    sel_r = lambda v: 'selected' if u['rol'] == v else ''
    body = f'''
    <div class="hrow"><h2>Editar usuario</h2><a href="/usuarios" class="btn b-gray">← Volver</a></div>
    <div class="card"><form method="POST">
      <label>Nombre *</label><input name="nombre" required value="{u["nombre"]}">
      <label>Email *</label><input type="email" name="email" required value="{u["email"]}">
      <label>Rol</label>
      <select name="rol">
        <option value="recepcionista" {sel_r("recepcionista")}>Recepcionista</option>
        <option value="admin" {sel_r("admin")}>Administrador</option>
      </select>
      <div class="factions">
        <a href="/usuarios" class="btn b-gray">Cancelar</a>
        <button type="submit" class="btn b-blue">Guardar cambios</button>
      </div>
    </form></div>'''
    return page(body)

@app.route('/usuarios/<int:id>/eliminar', methods=['POST'])
@login_required
def usuarios_eliminar(id):
    if id == session['user_id']:
        flash('No puedes eliminarte a ti mismo', 'error')
        return redirect('/usuarios')
    db = get_db()
    db.execute('DELETE FROM usuarios WHERE id=?', (id,))
    db.commit(); db.close()
    flash('Usuario eliminado', 'success')
    return redirect('/usuarios')

# ──────────────────────────────────────────────
if __name__ == '__main__':
    app.run(debug=True)
