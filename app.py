# app.py
import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import google.generativeai as genai

# Cargar variables de entorno desde el archivo .env (para desarrollo local)
load_dotenv()

app = Flask(__name__)

# --- Configuración de Gemini ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
model = None # Variable para almacenar el modelo de Gemini

if GEMINI_API_KEY:
    print("GEMINI_API_KEY encontrada. Configurando el SDK de Gemini...")
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        
        # Configuración del modelo
        generation_config = {
            "temperature": 0.7, # Controla la aleatoriedad de la respuesta
            "top_p": 1,
            "top_k": 1,
            "max_output_tokens": 2048, # Longitud máxima de la respuesta
        }
        safety_settings = [ # Configuraciones de seguridad
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        ]
        
        model = genai.GenerativeModel(model_name="gemini-pro", # Modelo adecuado para chat y texto general
                                      generation_config=generation_config,
                                      safety_settings=safety_settings)
        print("SDK de Gemini configurado y modelo 'gemini-pro' instanciado exitosamente.")
    except Exception as e:
        print(f"Error al configurar el SDK de Gemini o instanciar el modelo: {e}")
        model = None # Asegurar que el modelo no esté disponible si hay error
else:
    print("Advertencia: La variable de entorno GEMINI_API_KEY no está configurada.")
    print("La funcionalidad del chatbot con Gemini no estará disponible.")

@app.route('/')
def index():
    """
    Ruta principal que renderiza la interfaz del chat (templates/index.html).
    """
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat_endpoint():
    """
    Endpoint para recibir mensajes del usuario y devolver respuestas del modelo Gemini.
    """
    if not model:
        return jsonify({"error": "El modelo Gemini no está disponible o no se pudo inicializar."}), 500

    try:
        user_message = request.json.get('message')
        if not user_message:
            return jsonify({"error": "Mensaje vacío recibido."}), 400

        # Para gemini-pro, enviamos el contenido directamente.
        # Para un chat continuo, se gestionaría un historial de conversación.
        # Por ahora, cada mensaje es una nueva solicitud al modelo.
        prompt_parts = [user_message]
        response = model.generate_content(prompt_parts)
        
        bot_reply = response.text # Acceder al texto de la respuesta

        return jsonify({"reply": bot_reply})

    except Exception as e:
        # Capturar errores específicos de la API de Gemini si es posible
        error_message = str(e)
        # Podrías añadir un log más detallado aquí para el servidor
        print(f"Error al generar respuesta de Gemini: {error_message}")
        # Devolver un mensaje de error genérico al cliente
        return jsonify({"error": f"Error al procesar tu solicitud con el modelo: {error_message}"}), 500

if __name__ == '__main__':
    # El puerto se tomará de la variable de entorno PORT si está definida (útil para Databricks/PaaS)
    # o usará 5000 por defecto si no. Ajusta el default si es necesario (ej. 8080).
    port = int(os.environ.get('PORT', 5000))
    
    # Determinar el modo debug basado en FLASK_ENV
    # Por defecto a 'production' si FLASK_ENV no está seteado.
    is_debug_mode = os.getenv("FLASK_ENV", "production").lower() == "development"
    
    # Ejecutar la aplicación Flask.
    # host='0.0.0.0' hace que la app sea accesible desde cualquier IP.
    app.run(host='0.0.0.0', port=port, debug=is_debug_mode)
