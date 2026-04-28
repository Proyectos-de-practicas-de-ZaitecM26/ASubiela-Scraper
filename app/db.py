from flask import current_app
import sqlite3
from flask import g, current_app


# =========================
# BBDD BOE (solo oposiciones)
# =========================
def get_boe_db():
    db = getattr(g, "_boe_db", None)
    if db is None:
        db = g._boe_db = sqlite3.connect(current_app.config["BOE_DB_PATH"])
        db.row_factory = sqlite3.Row
    return db

# =========================
# BBDD Usuarios
# =========================
def get_users_db():
    db = getattr(g, "_users_db", None)
    if db is None:
        db = g._users_db = sqlite3.connect(current_app.config["USERS_DB_PATH"])
        db.row_factory = sqlite3.Row
    return db



# =========================
# Cierre conexiones
# =========================


def teardown_appcontext(exception):
    boe_db = getattr(g, "_boe_db", None)
    if boe_db is not None:
        boe_db.close()

    users_db = getattr(g, "_users_db", None)
    if users_db is not None:
        users_db.close()
