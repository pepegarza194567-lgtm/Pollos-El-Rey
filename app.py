from flask import Flask, render_template, request, redirect, url_for, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
from flask_mail import Mail, Message
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "polloselrey2025"

# ------------------------------------------
# 🔗 CONEXIÓN A MONGO DB ATLAS
# ------------------------------------------
MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise Exception("❌ ERROR: La variable MONGO_URI no está definida en Render")

try:
    cliente = MongoClient(MONGO_URI)
    cliente.admin.command("ping")
    print("✔ Conexión con MongoDB Atlas exitosa.")
except Exception as e:
    print("❌ ERROR de conexión con MongoDB:", e)
    raise Exception("No se pudo conectar a MongoDB Atlas.")

db = cliente["pollos_el_rey"]
productos_col = db["productos"]
pedidos_col = db["pedidos"]
mensajes_col = db["mensajes"]

# ------------------------------------------
# ✉️ CONFIGURACIÓN DE CORREO
# ------------------------------------------
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")
app.config['MAIL_DEFAULT_SENDER'] = ('Pollos El Rey', os.getenv("MAIL_USERNAME"))

mail = Mail(app)

# ------------------------------------------
# 🔥 RUTAS PRINCIPALES
# ------------------------------------------
@app.route('/')
def inicio():
    return render_template('index.html')

@app.route('/menu')
def menu():
    return render_template('menu.html')

@app.route('/promociones')
def promociones():
    return render_template('promociones.html')

@app.route('/nosotros')
def nosotros():
    return render_template('nosotros.html')

# ------------------------------------------
# ✉️ CONTACTO
# ------------------------------------------
@app.route('/contacto', methods=['GET', 'POST'])
def contacto():
    if request.method == 'POST':
        correo = request.form.get("correo", "").strip()
        asunto = request.form.get("asunto", "").strip()
        mensaje = request.form.get("mensaje", "").strip()

        if not correo or not asunto or not mensaje:
            flash("⚠️ Debes llenar todos los campos.", "warning")
            return redirect(url_for('contacto'))

        try:
            msg = Message(
                subject=f"Nuevo mensaje: {asunto}",
                recipients=[os.getenv("MAIL_USERNAME")],
                body=f"De: {correo}\n\nMensaje:\n{mensaje}"
            )
            mail.send(msg)

            mensajes_col.insert_one({
                "correo": correo,
                "asunto": asunto,
                "mensaje": mensaje,
                "fecha": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            })

            flash("✅ Tu mensaje fue enviado correctamente.", "success")
        except Exception as e:
            print("ERROR AL ENVIAR CORREO:", e)
            flash("❌ Error enviando el mensaje.", "danger")

        return redirect(url_for('contacto'))

    return render_template('contacto.html')

# ------------------------------------------
# 🛒 ORDENAR PLATILLO (CORREGIDO)
# ------------------------------------------
@app.route('/ordenar', methods=['POST'])
def ordenar():
    nombre = request.form.get("nombre", "").strip()
    telefono = request.form.get("telefono", "").strip()
    producto = request.form.get("producto", "").strip()
    precio = request.form.get("precio", "0").strip()
    imagen = request.form.get("imagen", "").strip()

    if not nombre or not telefono:
        flash("⚠️ Debes ingresar nombre y número.", "warning")
        return redirect(url_for('menu'))

    try:
        precio = float(precio)
    except:
        precio = 0.0

    pedido = {
        "cliente": nombre.title(),
        "telefono": telefono,
        "producto": producto if producto else "Sin especificar",
        "precio": precio,
        "imagen": imagen,
        "estado": "Pendiente",
        "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "comentario": ""
    }

    try:
        pedidos_col.insert_one(pedido)
        flash("✅ Pedido registrado correctamente.", "success")
    except Exception as e:
        print("❌ Error al guardar pedido:", e)
        flash("❌ Error guardando el pedido.", "danger")

    return redirect(url_for('mis_pedidos', telefono=telefono))

# ------------------------------------------
# 📦 MIS PEDIDOS
# ------------------------------------------
@app.route('/mis_pedidos')
def mis_pedidos():
    telefono = request.args.get("telefono", "")
    pedidos = list(pedidos_col.find({"telefono": telefono})) if telefono else []
    return render_template('mis_pedidos.html', pedidos=pedidos, telefono=telefono)

# ------------------------------------------
# 💬 GUARDAR COMENTARIO
# ------------------------------------------
@app.route('/guardar_comentario/<id>', methods=['POST'])
def guardar_comentario(id):
    comentario = request.form.get("comentario", "").strip()

    if not comentario:
        return "⚠️ Comentario vacío", 400

    pedidos_col.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"comentario": comentario}}
    )

    return "Comentario guardado correctamente", 200

# -------------------------------------------------------------
# 🚀 EJECUCIÓN (Render)
# -------------------------------------------------------------
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
