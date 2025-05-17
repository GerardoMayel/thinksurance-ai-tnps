# app.py
import os
import json # Importar json para manejar errores potenciales de Gemini
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import google.generativeai as genai

# Cargar variables de entorno del archivo .env (principalmente para desarrollo local)
# En Databricks, estas variables se establecerán a través de la configuración de la app/secretos.
load_dotenv()

app = Flask(__name__)

# --- Configuración de Gemini ---
# Obtener la clave API de Gemini de la variable de entorno.
# En Databricks, configura una variable de entorno llamada GEMINI_API_KEY
# y vincúlala a tu secreto de Databricks que contiene la clave (ej. 'secret' que mapea a 'token-gemini').
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("Advertencia: La variable de entorno GEMINI_API_KEY no está configurada.")
    # Podrías querer manejar esto de forma más robusta, por ejemplo, deshabilitando la funcionalidad del chat.
else:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        # Configuración del modelo
        # Para modelos 'gemini-pro', no se necesita system_instruction en generation_config
        # Si usas modelos más nuevos como gemini-1.5-flash, puedes añadir system_instruction
        generation_config = {
            "temperature": 0.7,
            "top_p": 1,
            "top_k": 1,
            "max_output_tokens": 2048,
        }
        safety_settings = [ # Configuraciones de seguridad
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        ]
        # Usaremos gemini-pro, que es un modelo de texto general.
        # Para chat, gemini-pro es adecuado. Si fuera un modelo específico de chat, podrías usar start_chat().
        model = genai.GenerativeModel(model_name="gemini-pro", # o "gemini-1.0-pro"
                                      generation_config=generation_config,
                                      safety_settings=safety_settings)
        print("Modelo Gemini configurado exitosamente.")
    except Exception as e:
        print(f"Error al configurar Gemini: {e}")
        model = None # Marcar que el modelo no está disponible


@app.route('/')
def index():
    """
    Ruta principal que renderiza la interfaz del chat.
    """
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """
    Endpoint para recibir mensajes del usuario y devolver respuestas del bot.
    """
    if not model:
        return jsonify({"error": "El modelo Gemini no está configurado o disponible."}), 500
    if not GEMINI_API_KEY: # Doble chequeo por si acaso
        return jsonify({"error": "API Key de Gemini no configurada en el servidor."}), 500

    try:
        user_message = request.json.get('message')
        if not user_message:
            return jsonify({"error": "Mensaje vacío"}), 400

        # Para gemini-pro, usamos generate_content directamente para interacciones simples.
        # Si tuvieras un historial de chat, lo construirías y lo pasarías.
        # Por ahora, cada mensaje es una nueva conversación.
        prompt_parts = [user_message]
        response = model.generate_content(prompt_parts)
        
        bot_reply = response.text # Acceder al texto de la respuesta

        return jsonify({"reply": bot_reply})

    except Exception as e:
        # Intentar obtener más detalles si es un error de la API de Gemini
        error_message = str(e)
        if hasattr(e, 'message'): # Algunos errores de API tienen un atributo 'message' más específico
             error_message = e.message
        
        print(f"Error al generar respuesta de Gemini: {error_message}") # Loguear el error en el servidor
        # Devolver un mensaje de error genérico al cliente
        return jsonify({"error": f"Error al procesar tu solicitud: {error_message}"}), 500

if __name__ == '__main__':
    # El puerto se tomará de la variable de entorno PORT si está definida (útil para Databricks/PaaS)
    # o usará 8080 por defecto si no. El comando en app.yaml ya maneja esto.
    port = int(os.environ.get('PORT', 8080))
    # debug=False es importante para producción. Flask lo toma de FLASK_ENV=production
    # host='0.0.0.0' para que sea accesible externamente.
    app.run(host='0.0.0.0', port=port, debug=(os.getenv("FLASK_ENV", "production").lower() == "development"))

