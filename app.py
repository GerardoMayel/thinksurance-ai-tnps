# app.py
import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
# import google.generativeai as genai # Descomentar cuando se integre Gemini
# import requests # Descomentar cuando se integre Databricks endpoint

# Cargar variables de entorno desde el archivo .env
load_dotenv()

app = Flask(__name__)

# Configuración inicial (ejemplos, se moverán a config.py o se usarán directamente de .env)
# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# DATABRICKS_ENDPOINT_URL = os.getenv("DATABRICKS_ENDPOINT_URL")
# DATABRICKS_API_TOKEN = os.getenv("DATABRICKS_API_TOKEN")
# ACTIVE_MODEL = os.getenv("ACTIVE_MODEL", "gemini") # Default to gemini

# Configurar Gemini (ejemplo, se activará después)
# if GEMINI_API_KEY:
#     genai.configure(api_key=GEMINI_API_KEY)

@app.route('/')
def index():
    """
    Ruta principal que renderiza la interfaz del chat.
    """
    # Por ahora, solo un mensaje simple.
    # Más adelante, renderizaremos una plantilla HTML.
    return "¡Hola! Soy tu chatbot Flask. ¡Despliegue inicial exitoso!"

# (Más adelante añadiremos la ruta /chat para la lógica del chatbot)

if __name__ == '__main__':
    # Obtener el puerto de la variable de entorno PORT, default a 5000 si no está definida.
    # Esto es útil para plataformas de despliegue que asignan puertos dinámicamente.
    port = int(os.environ.get('PORT', 5000))
    # Ejecutar la aplicación Flask.
    # debug=True es útil para desarrollo, pero debe ser False en producción.
    # host='0.0.0.0' hace que la app sea accesible desde cualquier IP, no solo localhost.
    app.run(host='0.0.0.0', port=port, debug=True)
