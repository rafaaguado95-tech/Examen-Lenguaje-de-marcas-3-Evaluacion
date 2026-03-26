# ============================================================
# database.py - Gestión de la base de datos SQLite
# ============================================================

import sqlite3
from flask import g
import os

DATABASE = 'taskflow.db'

def get_db():
    """Obtiene la conexión a la base de datos (una por request)"""
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row  # Permite acceder a columnas por nombre
    return g.db

def init_db():
    """Crea las tablas si no existen"""
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    
    db.executescript('''
        -- Tabla: Usuarios
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        -- Tabla: Proyectos
        CREATE TABLE IF NOT EXISTS proyectos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            descripcion TEXT,
            fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        -- Tabla: Tareas
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            descripcion TEXT,
            estado TEXT DEFAULT 'pendiente',  -- pendiente | en_progreso | completada
            fecha_limite DATE,
            fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
            proyecto_id INTEGER REFERENCES proyectos(id) ON DELETE SET NULL,
            asignado_a INTEGER REFERENCES usuarios(id) ON DELETE SET NULL
        );

        -- Tabla: Comentarios
        CREATE TABLE IF NOT EXISTS comentarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contenido TEXT NOT NULL,
            fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
            usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
            tarea_id INTEGER NOT NULL REFERENCES tareas(id) ON DELETE CASCADE
        );
    ''')
    db.commit()
    db.close()
