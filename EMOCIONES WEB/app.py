from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_mysqldb import MySQL
import cv2
import numpy as np
import os
from deepface import DeepFace
import MySQLdb.cursors
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from datetime import datetime, timedelta

app = Flask(__name__)

# 📌 Configuración de MySQL
app.config["MYSQL_HOST"] = "127.0.0.1"
app.config["MYSQL_PORT"] = 3306
app.config["MYSQL_USER"] = "alexis"
app.config["MYSQL_PASSWORD"] = "Montiel_alexis77"
app.config["MYSQL_DB"] = "mindvibe"

# 📌 Clave secreta para manejar sesiones
app.config["SECRET_KEY"] = "clave_super_secreta"

mysql = MySQL(app)

# 📌 Configuración de correo
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'mindvibe.app@gmail.com'  
app.config['MAIL_PASSWORD'] = 'imqx jsew cxtu qecn'  # usa contraseña de app si es Gmail

mail = Mail(app)

# 📌 Ruta para la pagina principal
@app.route('/')
def index():
    return render_template('principal.html')  # Cambia el nombre del archivo aquí

# 📌 Ruta para enviar correo de verificación
@app.route('/verificar_correo', methods=['POST'])
def verificar_correo():
    correo_usuario = request.form['correo']
    
    msg = Message('🌟 Verificación de correo - MindVibe',
                  sender=app.config['MAIL_USERNAME'],
                  recipients=[correo_usuario])
    
    msg.html = f"""
    <html>
        <body style="font-family: Arial, sans-serif; background-color: #f9f9f9; padding: 20px;">
            <div style="max-width: 600px; margin: auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1);">
                <h2 style="color: #00BFA6;">¡Hola 👋!</h2>
                <p>Gracias por registrarte en <strong>MindVibe</strong> 💡.</p>
                <p>Este es un mensaje de verificación para asegurarnos de que tu correo <strong>{correo_usuario}</strong> está activo.</p>
                <p style="margin-top: 20px;">Si tú no solicitaste esta verificación, puedes ignorar este correo.</p>
                <hr>
                <p style="font-size: 12px; color: gray;">Este es un mensaje automático, por favor no respondas a este correo.</p>
            </div>
        </body>
    </html>
    """

    try:
        mail.send(msg)
        return "Correo personalizado enviado con éxito ✅"
    except Exception as e:
        return f"Error al enviar el correo: {str(e)}"


# 📌 Carpeta de subida
UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# 📌 Función corregida para analizar emoción
def analyze_emotion(image_path):
    try:
        image = cv2.imread(image_path)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        if len(faces) == 0:
            return None  # No se detectaron caras
        analysis = DeepFace.analyze(img_path=image_path, actions=["emotion"], enforce_detection=True)
        if isinstance(analysis, list) and len(analysis) > 0:
            return analysis[0]["dominant_emotion"]
        return None
    except Exception as e:
        print(f"[❌ Error de análisis]: {e}")
        return None  # No regreses el string de error aquí

# 📌 Chatbot según emoción
def chatbot_response(emotion):
    responses = {
        "happy": "¡Genial! Sigue disfrutando tu día. 😊",
        "sad": "Parece que estás triste. ¿Quieres escuchar música relajante? 🎶",
        "angry": "Respira profundo. ¿Te gustaría hacer una actividad para calmarte? 🧘",
        "surprise": "¡Vaya! Algo inesperado pasó. ¿Quieres compartirlo? 🤔",
        "fear": "Todo estará bien. Trata de relajarte un poco. 💙",
        "neutral": "Todo parece tranquilo. ¡Sigue adelante! 🚀",
        "disgust": "Algo te desagrada. Tal vez hablar de ello te ayude. 🧐",
        "contempt": "Pareces molesto. ¿Qué te gustaría hacer para relajarte? 🤨"
    }
    return responses.get(emotion, "No pude detectar la emoción. Inténtalo de nuevo.")

# 📌 Ruta principal (registro)
@app.route('/formulario')
def formulario():
    return render_template('formulario.html')

# 📌 Guardar usuario
@app.route('/guardar', methods=['POST'])
def guardar():
    nombre = request.form['nombre']
    correo = request.form['correo']
    contraseña = request.form['contraseña']
    hashed_password = generate_password_hash(contraseña)
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO usuarios (nombre, correo, contraseña) VALUES (%s, %s, %s)", 
                (nombre, correo, hashed_password))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('login'))

# 📌 Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST':
        correo = request.form['correo']
        contraseña = request.form['contraseña']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM usuarios WHERE correo = %s', (correo,))
        usuario = cursor.fetchone()
        if usuario and check_password_hash(usuario['contraseña'], contraseña):
            session['usuario_id'] = usuario['id']
            session['nombre'] = usuario['nombre']
            return redirect(url_for('detectar'))
        else:
            msg = '⚠️ Credenciales incorrectas. Intenta de nuevo.'
    return render_template('login.html', msg=msg)

# 📌 Cerrar sesión
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# 📌 Página de detección (index.html)
@app.route('/detectar', methods=['GET'])
def detectar():
    if 'nombre' in session:
        return render_template("index.html", usuario=session['nombre'])
    return redirect(url_for('login'))

# 📌 Análisis de emociones (POST con imagen)
@app.route("/analyze", methods=["POST"])
def analyze():
    if "file" not in request.files:
        return jsonify({"error": "No se envió ninguna imagen"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Nombre de archivo vacío"}), 400
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(file_path)
    emotion = analyze_emotion(file_path)
    if emotion is None:
        return jsonify({"error": "No se detectó un rostro humano. Por favor, sube una imagen válida."}), 400
    message = chatbot_response(emotion)
    if 'usuario_id' in session:
        user_id = session['usuario_id']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO emociones (usuario_id, emocion) VALUES (%s, %s)", 
                    (user_id, emotion))
        mysql.connection.commit()
        cur.close()
    return jsonify({"emotion": emotion, "message": message})

# 📌 Estadísticas de emociones
@app.route('/estadisticas')
def estadisticas():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    filtro = request.args.get('filtro', 'dia')  # por defecto 'dia'

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    hoy = datetime.today()

    if filtro == 'dia':
        fecha_inicio = hoy.date()
    elif filtro == 'semana':
        fecha_inicio = hoy - timedelta(days=7)
    elif filtro == '15dias':
        fecha_inicio = hoy - timedelta(days=15)
    elif filtro == 'mes':
        fecha_inicio = hoy - timedelta(days=30)
    else:
        fecha_inicio = hoy - timedelta(days=1)  # por defecto día

    cursor.execute("""
        SELECT emocion, COUNT(*) as total 
        FROM emociones 
        WHERE usuario_id = %s AND fecha >= %s 
        GROUP BY emocion
    """, (session['usuario_id'], fecha_inicio))

    resultados = cursor.fetchall()
    emociones_validas = ['happy', 'sad', 'angry', 'surprise', 'fear', 'neutral', 'disgust', 'contempt']

    emociones = []
    totales = []
    for fila in resultados:
        if fila['emocion'] in emociones_validas:
            emociones.append(fila['emocion'])
            totales.append(fila['total'])


    return render_template('estadisticas.html', emociones=emociones, totales=totales, filtro=filtro)

# 📌 Ejecutar app
if __name__ == "__main__":
    app.run(debug=True)
