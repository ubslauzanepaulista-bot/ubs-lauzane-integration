from flask_jwt_extended import create_access_token
import bcrypt
import psycopg2
import os

DATABASE_URL = os.getenv("DATABASE_URL")

def conectar():
    return psycopg2.connect(DATABASE_URL)

def autenticar(username, senha):
    conn = conectar()
    cur = conn.cursor()

    cur.execute("SELECT password, role FROM usuarios WHERE username=%s", (username,))
    result = cur.fetchone()

    cur.close()
    conn.close()

    if result:
        senha_hash, role = result

        if bcrypt.checkpw(senha.encode(), senha_hash.encode()):
            token = create_access_token(identity={
                "username": username,
                "role": role
            })
            return token

    return None