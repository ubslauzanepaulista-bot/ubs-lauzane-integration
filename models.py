from flask import Flask, request, render_template, jsonify
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
import bcrypt
import datetime
import requests
import os
from models import conectar, criar_tabelas
from auth import autenticar
from dotenv import load_dotenv

# ===== LOAD ENV =====
load_dotenv()

app = Flask(__name__)

# ===== CONFIG SEGURA =====
app.secret_key = os.getenv("SECRET_KEY")
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")

jwt = JWTManager(app)

# ===== BANCO =====
criar_tabelas()

# ===== VARIÁVEIS =====
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")

# ================= REGISTER =================
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    if not data or not data.get("username") or not data.get("password") or not data.get("role"):
        return jsonify({"erro": "Dados inválidos"}), 400

    senha_hash = bcrypt.hashpw(
        data["password"].encode(),
        bcrypt.gensalt()
    ).decode()

    try:
        conn = conectar()
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO usuarios (username, password, role) VALUES (%s,%s,%s)",
            (data["username"], senha_hash, data["role"])
        )

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"msg": "Usuário criado"})

    except Exception as e:
        return jsonify({"erro": "Usuário já existe ou erro no banco"}), 400

# ================= LOGIN =================
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    if not data or not data.get("username") or not data.get("password"):
        return jsonify({"erro": "Dados inválidos"}), 400

    token = autenticar(data["username"], data["password"])

    if token:
        return jsonify({"token": token})

    return jsonify({"erro": "Login inválido"}), 401

# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

# ================= DADOS =================
@app.route("/dados")
@jwt_required()
def dados():
    user = get_jwt_identity()

    conn = conectar()
    cur = conn.cursor()

    if user["role"] == "admin":
        cur.execute("SELECT * FROM envios ORDER BY data DESC")
    else:
        cur.execute("SELECT * FROM envios WHERE usuario=%s", (user["username"],))

    rows = cur.fetchall()

    cur.close()
    conn.close()

    colunas = ["id", "usuario", "nome", "telefone", "status", "data"]
    dados = [dict(zip(colunas, row)) for row in rows]

    return jsonify(dados)

# ================= ENVIAR =================
@app.route("/enviar", methods=["POST"])
@jwt_required()
def enviar():
    user = get_jwt_identity()
    data = request.get_json()

    if not data or not data.get("telefone") or not data.get("mensagem"):
        return jsonify({"erro": "Dados inválidos"}), 400

    numero = data["telefone"]

    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"

    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "text",
        "text": {"body": data["mensagem"]}
    }

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    r = requests.post(url, headers=headers, json=payload, timeout=10)

    status = "ENVIADO" if r.status_code == 200 else "ERRO"

    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO envios (usuario, nome, telefone, status, data)
    VALUES (%s,%s,%s,%s,%s)
    """, (user["username"], data.get("nome", ""), numero, status, datetime.datetime.now()))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"status": status})

# ================= WEBHOOK =================
@app.route("/webhook", methods=["GET", "POST"])
def webhook():

    # 🔐 VERIFICAÇÃO META
    if request.method == "GET":
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge")
        return "erro"

    # 📩 RECEBER RESPOSTAS
    data = request.json

    try:
        msg = data["entry"][0]["changes"][0]["value"]["messages"][0]
        numero = msg["from"]

        if "button" in msg:
            resposta = msg["button"]["payload"]
        elif "text" in msg:
            texto = msg["text"]["body"].lower()
            if "confirm" in texto:
                resposta = "CONFIRMADO"
            elif "cancel" in texto:
                resposta = "CANCELADO"
            else:
                resposta = "OUTRO"
        else:
            resposta = "OUTRO"

        status = "CONFIRMADO" if resposta == "CONFIRMADO" else "CANCELADO"

        conn = conectar()
        cur = conn.cursor()

        cur.execute("""
        INSERT INTO envios (usuario, nome, telefone, status, data)
        VALUES (%s,%s,%s,%s,%s)
        """, ("paciente", numero, numero, status, datetime.datetime.now()))

        conn.commit()
        cur.close()
        conn.close()

    except Exception as e:
        print("Erro webhook:", e)

    return "ok"

# ================= RUN =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
