# app.py
import os
from flask import Flask, render_template, request, jsonify # render_template, request, jsonify no se usan aún pero se pueden dejar
from dotenv import load_dotenv
import google.generativeai as genai # Importar la librería de Gemini

# Cargar variables de entorno desde el archivo .env (útil para desarrollo local)
# En Databricks, estas variables se establecerán a través de la configuración de la app/secretos.
load_dotenv()

app = Flask(__name__)

# --- Debug: Imprimir todas las variables de entorno en consola (se mantiene por si es útil) ---
print("="*30)
print("Variables de Entorno Disponibles (Consola):")
for key, value in os.environ.items():
    print(f"{key}: {value}")
print("="*30)
# --- Fin Debug Consola ---

# --- Configuración de Gemini ---
# Obtener la clave API de Gemini de la variable de entorno.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

gemini_sdk_configured_message = "No intentada."
gemini_model_instance_message = "No intentada."

if GEMINI_API_KEY:
    print(f"GEMINI_API_KEY encontrada en las variables de entorno. Valor: '{GEMINI_API_KEY[:5]}...' (primeros 5 caracteres)")
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_sdk_configured_message = "SDK de Gemini configurado exitosamente."
        print(gemini_sdk_configured_message)
        # Aquí podrías inicializar el modelo si quisieras, por ejemplo:
        # model = genai.GenerativeModel('gemini-pro')
        # gemini_model_instance_message = "Modelo Gemini ('gemini-pro') instanciado."
        # print(gemini_model_instance_message)
    except Exception as e:
        error_msg = f"Error al configurar el SDK de Gemini o instanciar el modelo: {e}"
        gemini_sdk_configured_message = error_msg
        print(error_msg)
else:
    warning_msg = "Advertencia: La variable de entorno GEMINI_API_KEY no está configurada o está vacía."
    gemini_sdk_configured_message = warning_msg
    gemini_model_instance_message = "La funcionalidad de Gemini no estará disponible."
    print(warning_msg)
    print(gemini_model_instance_message)

@app.route('/')
def index():
    """
    Ruta principal que muestra información de bienvenida, estado de API y variables de entorno.
    """
    # Recopilar variables de entorno para mostrarlas en HTML
    env_vars_html = "<ul>"
    for key, value in sorted(os.environ.items()): # Ordenadas para mejor visualización
        env_vars_html += f"<li><strong>{key}:</strong> {value}</li>"
    env_vars_html += "</ul>"

    # Verificar disponibilidad del modelo Gemini
    gemini_model_available = False
    gemini_check_message = "No se pudo verificar el modelo (API Key no configurada o error previo)."
    if GEMINI_API_KEY and 'genai' in globals() and hasattr(genai, 'get_model'):
        try:
            genai.get_model('models/gemini-pro') # Intenta obtener un modelo para verificar
            gemini_model_available = True
            gemini_check_message = "Modelo 'models/gemini-pro' accesible."
        except Exception as e:
            gemini_check_message = f"Error al verificar el modelo de Gemini ('models/gemini-pro'): {e}"
            print(gemini_check_message) # También imprimir en consola para logs
            gemini_model_available = False
            
    api_status_page = "configurada y lista" if gemini_model_available else "NO configurada o con errores"

    # Construir el HTML
    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Chatbot Flask - Estado</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f4f4f4; color: #333; }}
            .container {{ background-color: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
            h1 {{ color: #333; }}
            h2 {{ color: #555; border-bottom: 1px solid #eee; padding-bottom: 5px; }}
            ul {{ list-style-type: none; padding-left: 0; }}
            li {{ background-color: #f9f9f9; margin-bottom: 8px; padding: 10px; border-radius: 4px; word-wrap: break-word; }}
            strong {{ color: #007bff; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>¡Hola! Soy tu chatbot Flask.</h1>
            <p>Despliegue inicial exitoso.</p>
            
            <h2>Estado de la API de Gemini</h2>
            <p><strong>Configuración del SDK:</strong> {gemini_sdk_configured_message}</p>
            <p><strong>Verificación del Modelo ('models/gemini-pro'):</strong> {gemini_check_message}</p>
            <p><strong>Estado General API para la página:</strong> {api_status_page}</p>
            
            <h2>Variables de Entorno Disponibles para la Aplicación</h2>
            {env_vars_html}
        </div>
    </body>
    </html>
    """
    return html_content

# (Más adelante añadiremos la ruta /chat para la lógica del chatbot)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    is_debug_mode = os.getenv("FLASK_ENV", "production").lower() == "development"
    app.run(host='0.0.0.0', port=port, debug=is_debug_mode)
