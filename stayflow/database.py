# ============================================================
# database.py - Base de datos SQLite para StayFlow
# ============================================================

import sqlite3
from flask import g

DATABASE = 'stayflow.db'

def get_db():
    """Devuelve la conexión activa (una por request)"""
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row  # acceder columnas por nombre
    return g.db

def init_db():
    """Crea todas las tablas si no existen"""
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    db.executescript('''

        CREATE TABLE IF NOT EXISTS usuarios (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre     TEXT NOT NULL,
            email      TEXT UNIQUE NOT NULL,
            password   TEXT NOT NULL,
            rol        TEXT DEFAULT 'recepcionista',
            fecha_alta DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS huespedes (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre       TEXT NOT NULL,
            apellidos    TEXT NOT NULL,
            email        TEXT,
            telefono     TEXT,
            dni          TEXT,
            nacionalidad TEXT,
            fecha_alta   DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS habitaciones (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            numero       TEXT UNIQUE NOT NULL,
            tipo         TEXT NOT NULL,
            precio_noche REAL NOT NULL,
            capacidad    INTEGER DEFAULT 2,
            estado       TEXT DEFAULT 'disponible',
            descripcion  TEXT
        );

        CREATE TABLE IF NOT EXISTS reservas (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            huesped_id    INTEGER NOT NULL REFERENCES huespedes(id) ON DELETE CASCADE,
            habitacion_id INTEGER NOT NULL REFERENCES habitaciones(id) ON DELETE CASCADE,
            fecha_entrada DATE NOT NULL,
            fecha_salida  DATE NOT NULL,
            estado        TEXT DEFAULT 'confirmada',
            total         REAL DEFAULT 0,
            notas         TEXT,
            fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS servicios (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            reserva_id INTEGER NOT NULL REFERENCES reservas(id) ON DELETE CASCADE,
            nombre     TEXT NOT NULL,
            precio     REAL NOT NULL,
            cantidad   INTEGER DEFAULT 1,
            fecha      DATETIME DEFAULT CURRENT_TIMESTAMP
        );

    ''')
    db.commit()
    db.close()
