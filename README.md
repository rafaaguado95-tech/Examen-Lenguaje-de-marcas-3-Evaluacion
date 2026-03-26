# 🏨 StayFlow - Gestión Hotelera

Aplicación web SaaS desarrollada con **Flask + SQLite + Jinja2**.

---

## 📁 Estructura del proyecto

```
stayflow/
├── app.py              ← Rutas Flask (controlador principal)
├── database.py         ← Conexión y creación de tablas SQLite
├── requirements.txt    ← Dependencias Python
├── stayflow.db         ← Base de datos SQLite (se crea sola)
├── static/
│   ├── css/style.css
│   └── js/main.js
└── templates/
    ├── base.html        ← Plantilla base con sidebar
    ├── login.html
    ├── dashboard.html
    ├── huespedes/
    │   ├── lista.html
    │   └── form.html
    ├── habitaciones/
    │   ├── lista.html
    │   └── form.html
    ├── reservas/
    │   ├── lista.html
    │   ├── form.html
    │   └── detalle.html
    └── usuarios/
        ├── lista.html
        └── form.html
```

---

## 🚀 Instalación y ejecución

### 1. Instalar dependencias
```bash
python -m pip install -r requirements.txt
```

### 2. Ejecutar
```bash
python app.py
```

### 3. Abrir en el navegador
```
http://127.0.0.1:5000
```

### Credenciales por defecto
- **Email:** admin@stayflow.com
- **Contraseña:** admin123

---

## 🗄️ Entidades y CRUD

| Entidad      | Crear | Leer | Actualizar | Eliminar |
|--------------|-------|------|------------|---------|
| Usuarios     | ✅    | ✅   | ✅         | ✅      |
| Huéspedes    | ✅    | ✅   | ✅         | ✅      |
| Habitaciones | ✅    | ✅   | ✅         | ✅      |
| Reservas     | ✅    | ✅   | ✅         | ✅      |
| Servicios    | ✅    | ✅   | —          | ✅      |

---

## ⚙️ Funcionalidades

- ✅ Login con contraseñas hasheadas (werkzeug)
- ✅ Usuario admin creado automáticamente al arrancar
- ✅ Dashboard con estadísticas en tiempo real
- ✅ CRUD completo de las 4 entidades principales
- ✅ Servicios extra por reserva (minibar, spa, lavandería...)
- ✅ Total calculado automáticamente (noches × precio/noche)
- ✅ Filtros por estado en reservas y habitaciones
- ✅ Búsqueda de huéspedes por nombre/DNI
- ✅ Sidebar de navegación fija

---

## 🔑 Rutas principales

| Ruta                          | Método   | Función                  |
|-------------------------------|----------|--------------------------|
| `/login`                      | GET/POST | Inicio de sesión         |
| `/dashboard`                  | GET      | Panel principal          |
| `/huespedes`                  | GET      | Listar huéspedes         |
| `/huespedes/nuevo`            | GET/POST | Crear huésped            |
| `/huespedes/editar/<id>`      | GET/POST | Editar huésped           |
| `/huespedes/eliminar/<id>`    | POST     | Eliminar huésped         |
| `/habitaciones`               | GET      | Listar habitaciones      |
| `/habitaciones/nueva`         | GET/POST | Crear habitación         |
| `/reservas`                   | GET      | Listar reservas          |
| `/reservas/nueva`             | GET/POST | Crear reserva            |
| `/reservas/detalle/<id>`      | GET      | Ver reserva + servicios  |
| `/servicios/nuevo/<reserva_id>` | POST   | Añadir servicio extra    |
| `/usuarios`                   | GET      | Listar usuarios          |
