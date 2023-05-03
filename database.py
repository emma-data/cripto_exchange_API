import sqlite3


def conexion():
    conn = sqlite3.connect("users.db")
    return conn


def crear_tablas():
    conn = conexion()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users 
                    (id INTEGER PRIMARY KEY, balance REAL DEFAULT 0)""")
    c.execute("""CREATE TABLE IF NOT EXISTS transactions 
                    (id INTEGER PRIMARY KEY, user_id INTEGER, asset TEXT, quantity REAL, price REAL, datetime TEXT, type TEXT)""")
    conn.commit()


