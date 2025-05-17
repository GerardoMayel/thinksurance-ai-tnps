# app.py
import os
from flask import Flask, render_template, request, jsonify # render_template, request, jsonify no se usan aún pero se pueden dejar
from dotenv import load_dotenv
import google.generativeai as genai # Importar la librería de Gemini

# Cargar variables de entorno desde el archivo .env (útil para desarrollo local)
# En Databricks, estas variables se establecerán a través de la configuración de la app/secretos.
load_dotenv()

app = Flask(__name__)

# --- Configuración de Gemini ---
# Obtener la clave API de Gemini de la variable de entorno.
# En Databricks, configura una variable de entorno llamada GEMINI_API_KEY
# y vincúlala a tu secreto de Databricks que contiene la clave.
GEMINI_API_KEY = os.getenv("secret")

if GEMINI_API_KEY:
    print("GEMINI_API_KEY encontrada en las variables de entorno.")
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        print("SDK de Gemini configurado exitosamente.")
        # Aquí podrías inicializar el modelo si quisieras, por ejemplo:
        # model = genai.GenerativeModel('gemini-pro')
        # print("Modelo Gemini ('gemini-pro') instanciado.")
    except Exception as e:
        print(f"Error al configurar el SDK de Gemini o instanciar el modelo: {e}")
else:
    print("Advertencia: La variable de entorno GEMINI_API_KEY no está configurada.")
    print("La funcionalidad de Gemini no estará disponible.")

@app.route('/')
def index():
    """
    Ruta principal que renderiza la interfaz del chat.
    """
    # Por ahora, solo un mensaje simple.
    # Más adelante, renderizaremos una plantilla HTML.
    api_status = "configurada y lista" if GEMINI_API_KEY and 'genai' in globals() and genai.get_model('models/gemini-pro') else "NO configurada o con errores"
    return f"¡Hola! Soy tu chatbot Flask. ¡Despliegue inicial exitoso! Estado de la API de Gemini: {api_status}."

# (Más adelante añadiremos la ruta /chat para la lógica del chatbot)

if __name__ == '__main__':
    # Obtener el puerto de la variable de entorno PORT, default a 5000 si no está definida.
    port = int(os.environ.get('PORT', 5000))
    # Determinar el modo debug basado en FLASK_ENV
    is_debug_mode = os.getenv("FLASK_ENV", "production").lower() == "development"
    
    # Ejecutar la aplicación Flask.
    # host='0.0.0.0' hace que la app sea accesible desde cualquier IP.
    app.run(host='0.0.0.0', port=port, debug=is_debug_mode)
