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
# Intenta usar un modelo más reciente y eficiente como gemini-1.5-flash-latest
# o puedes usar "gemini-1.0-pro-latest" o "gemini-pro" si prefieres.
# MODEL_NAME = "gemini-1.0-pro" # Modelo anterior
MODEL_NAME = "gemini-1.5-flash-latest"


if GEMINI_API_KEY:
    print(f"GEMINI_API_KEY encontrada. Configurando el SDK de Gemini para el modelo: {MODEL_NAME}...")
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        
        # Configuración del modelo
        generation_config = {
            "temperature": 0.7, # Controla la aleatoriedad de la respuesta
            "top_p": 0.95, # Ajustado ligeramente, común para modelos más nuevos
            "top_k": 0, # Ajustado, a menudo se prefiere top_p solo o top_k más alto
            "max_output_tokens": 2048, # Longitud máxima de la respuesta
        }
        safety_settings = [ # Configuraciones de seguridad
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        ]
        
        model = genai.GenerativeModel(model_name=MODEL_NAME,
                                      generation_config=generation_config,
                                      safety_settings=safety_settings)
        print(f"SDK de Gemini configurado y modelo '{MODEL_NAME}' instanciado exitosamente.")
    except Exception as e:
        print(f"Error al configurar el SDK de Gemini o instanciar el modelo '{MODEL_NAME}': {e}")
        model = None # Asegurar que el modelo no esté disponible si hay error
else:
    print("Advertencia: La variable de entorno GEMINI_API_KEY no está configurada.")
    print("La funcionalidad del chatbot con Gemini no estará disponible.")

@app.route('/')
def index():
    """
    Ruta principal que renderiza la interfaz del chat (templates/index.html).
    """
    # Asegúrate de que la carpeta 'templates' exista en el mismo nivel que app.py
    # y que 'index.html' esté dentro de 'templates'.
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat_endpoint():
    """
    Endpoint para recibir mensajes del usuario y devolver respuestas del modelo Gemini.
    """
    print("\n--- Nueva Solicitud a /chat ---") # Log para inicio de solicitud
    if not model:
        print("Error en /chat: El modelo Gemini no está disponible.")
        return jsonify({"error": "El modelo Gemini no está disponible o no se pudo inicializar."}), 500

    try:
        data = request.get_json() # Es mejor usar get_json() para manejar errores de formato
        if not data or 'message' not in data:
            print("Error en /chat: JSON inválido o falta 'message'.")
            return jsonify({"error": "Solicitud JSON inválida o falta el campo 'message'."}), 400
        
        user_message = data['message']
        if not user_message.strip(): # Comprobar si el mensaje está vacío o solo espacios
            print("Error en /chat: Mensaje vacío recibido.")
            return jsonify({"error": "Mensaje vacío recibido."}), 400

        print(f"Mensaje recibido del usuario: '{user_message}'")

        # Para gemini-pro y modelos flash, enviamos el contenido directamente.
        # Para un chat continuo, se gestionaría un historial de conversación.
        prompt_parts = [user_message]
        
        print(f"Enviando al modelo {MODEL_NAME}: '{prompt_parts}'")
        response = model.generate_content(prompt_parts)
        
        # Debug: Imprimir la respuesta completa del modelo si es necesario
        # print(f"Respuesta completa del modelo: {response}")

        if not response.parts:
             print("Advertencia: La respuesta del modelo no tiene partes de contenido.")
             bot_reply = "No pude generar una respuesta esta vez."
        elif hasattr(response, 'text'):
            bot_reply = response.text
        else:
            # Intenta extraer texto de las partes si .text no está directamente disponible
            # Esto es más para modelos multimodales, pero es un fallback
            try:
                bot_reply = "".join(part.text for part in response.parts if hasattr(part, 'text'))
                if not bot_reply.strip():
                    bot_reply = "Recibí una respuesta, pero no contenía texto legible."
            except Exception as ex_parts:
                print(f"Error extrayendo texto de las partes de la respuesta: {ex_parts}")
                bot_reply = "Error al procesar la respuesta del modelo."


        print(f"Respuesta generada por el bot: '{bot_reply}'")
        return jsonify({"reply": bot_reply})

    except Exception as e:
        error_message = str(e)
        print(f"Error crítico en /chat al generar respuesta de Gemini: {error_message}")
        # Para errores de API específicos, a veces el error 'e' tiene más detalles.
        # Por ejemplo, e.args o e.message
        # Devolver un mensaje de error genérico al cliente
        return jsonify({"error": f"Error al procesar tu solicitud con el modelo: {error_message}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    is_debug_mode = os.getenv("FLASK_ENV", "production").lower() == "development"
    
    print(f"Iniciando servidor Flask en host 0.0.0.0 puerto {port}, debug={is_debug_mode}")
    app.run(host='0.0.0.0', port=port, debug=is_debug_mode)
