# ⚡ TaskFlow - Gestión de Tareas SaaS

Aplicación web SaaS desarrollada con **Flask + SQLite + Jinja2**.

---

## 📁 Estructura del proyecto

```
taskflow/
├── app.py              ← Rutas Flask (controlador)
├── database.py         ← Conexión y creación de tablas SQLite
├── requirements.txt    ← Dependencias Python
├── taskflow.db         ← Base de datos SQLite (se crea sola)
├── static/
│   ├── css/style.css   ← Estilos
│   └── js/main.js      ← JavaScript básico
└── templates/
    ├── base.html        ← Plantilla base con navbar
    ├── login.html
    ├── register.html
    ├── dashboard.html
    ├── tareas/
    │   ├── lista.html
    │   ├── form.html
    │   └── detalle.html
    ├── proyectos/
    │   ├── lista.html
    │   └── form.html
    └── usuarios/
        ├── lista.html
        └── editar.html
```

---

## 🚀 Instalación y ejecución

### 1. Crear entorno virtual (recomendado)
```bash
python -m venv venv

# Windows:
venv\Scripts\activate

# Linux/Mac:
source venv/bin/activate
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Ejecutar la aplicación
```bash
python app.py
```

### 4. Abrir en el navegador
```
http://127.0.0.1:5000
```

---

## 🗄️ Entidades y CRUD

| Entidad      | Crear | Leer | Actualizar | Eliminar |
|--------------|-------|------|------------|---------|
| Usuarios     | ✅    | ✅   | ✅         | ✅      |
| Tareas       | ✅    | ✅   | ✅         | ✅      |
| Proyectos    | ✅    | ✅   | ✅         | ✅      |
| Comentarios  | ✅    | ✅   | —          | ✅      |

---

## ⚙️ Funcionalidades

- ✅ Registro e inicio de sesión con contraseñas hasheadas
- ✅ Panel de estadísticas (dashboard)
- ✅ CRUD completo de tareas, proyectos, usuarios y comentarios
- ✅ Asignación de tareas a usuarios
- ✅ Filtrar tareas por estado
- ✅ Marcar tareas como completadas (toggle)
- ✅ Comentarios en tareas
- ✅ Sugerencia de título con IA (requiere API key)

---

## 🤖 Extra: Sugerencia con IA

Para activar la sugerencia automática de títulos, añade tu API key de Anthropic:

```bash
# Linux/Mac:
export ANTHROPIC_API_KEY=tu_api_key_aqui

# Windows (CMD):
set ANTHROPIC_API_KEY=tu_api_key_aqui
```

Sin la key, el botón "✨ Sugerir con IA" simplemente no funcionará.

---

## 🔑 Rutas principales

| Ruta                        | Método   | Función                    |
|-----------------------------|----------|----------------------------|
| `/login`                    | GET/POST | Inicio de sesión           |
| `/register`                 | GET/POST | Registro                   |
| `/dashboard`                | GET      | Panel principal            |
| `/tareas`                   | GET      | Listar tareas              |
| `/tareas/nueva`             | GET/POST | Crear tarea                |
| `/tareas/editar/<id>`       | GET/POST | Editar tarea               |
| `/tareas/eliminar/<id>`     | POST     | Eliminar tarea             |
| `/tareas/completar/<id>`    | POST     | Toggle completar           |
| `/tareas/detalle/<id>`      | GET      | Ver tarea + comentarios    |
| `/proyectos`                | GET      | Listar proyectos           |
| `/proyectos/nuevo`          | GET/POST | Crear proyecto             |
| `/usuarios`                 | GET      | Listar usuarios            |
| `/api/sugerir-titulo`       | POST     | IA: sugerir título         |
