# app.py
import os
import requests # Para hacer llamadas HTTP al endpoint de Databricks
import json     # Para manejar datos JSON
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env (para desarrollo local)
# En Databricks, estas se configurarán en el entorno de la aplicación.
load_dotenv()

app = Flask(__name__)

# --- Configuración del Endpoint de Databricks Llama ---
DATABRICKS_ENDPOINT_URL = os.getenv("DATABRICKS_ENDPOINT_URL")
DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN")
# El nombre del modelo que espera tu endpoint específico.
# Puede ser parte de la URL del endpoint o requerido en el payload.
# Basado en tu URL, el endpoint es para "databricks-llama-4-maverick".
LLAMA_MODEL_NAME = os.getenv("LLAMA_MODEL_NAME", "databricks-llama-4-maverick")


# Verificar configuración al iniciar
if not DATABRICKS_ENDPOINT_URL:
    print("Advertencia: La variable de entorno DATABRICKS_ENDPOINT_URL no está configurada.")
if not DATABRICKS_TOKEN:
    print("Advertencia: La variable de entorno DATABRICKS_TOKEN no está configurada.")
if DATABRICKS_ENDPOINT_URL and DATABRICKS_TOKEN:
    print(f"Configuración para Databricks Llama endpoint '{DATABRICKS_ENDPOINT_URL}' lista.")
    print(f"Usando el modelo en payload: {LLAMA_MODEL_NAME}")


@app.route('/')
def index():
    """
    Ruta principal que renderiza la interfaz del chat (templates/index.html).
    El archivo index.html ya contiene el mensaje inicial del bot.
    """
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat_endpoint():
    """
    Endpoint para recibir mensajes del usuario y devolver respuestas del modelo Llama
    desplegado en Databricks.
    """
    print("\n--- Nueva Solicitud a /chat (Databricks Llama) ---")

    if not DATABRICKS_ENDPOINT_URL or not DATABRICKS_TOKEN:
        print("Error en /chat: DATABRICKS_ENDPOINT_URL o DATABRICKS_TOKEN no configurados en el servidor.")
        return jsonify({"error": "El servicio de IA no está configurado correctamente en el servidor."}), 500

    try:
        data = request.get_json()
        if not data or 'message' not in data:
            print("Error en /chat: JSON inválido o falta 'message'.")
            return jsonify({"error": "Solicitud JSON inválida o falta el campo 'message'."}), 400
        
        user_message = data['message'] # Esta es la calificación o respuesta del usuario
        if not user_message.strip():
            print("Error en /chat: Mensaje vacío recibido.")
            return jsonify({"error": "Mensaje vacío recibido."}), 400

        print(f"Mensaje (calificación/respuesta) recibido del usuario: '{user_message}'")

        # System prompt para guiar al modelo Llama a hacer la pregunta abierta después de la calificación
        system_prompt = (
            "Eres un asistente virtual de Zurich Santander. Un cliente acaba de proporcionar una calificación numérica "
            "en una escala del 0 al 10 sobre si recomendaría el servicio, en respuesta a la pregunta "
            "'Hola 👋 ¿En una escala del 1 al 10 nos recomendarías?'. "
            "Tu tarea es agradecerle brevemente por su respuesta (la calificación que te acaba de dar) y luego hacer la pregunta abierta estándar de NPS: "
            "'Gracias por tu calificación. ¿Podrías contarnos un poco más sobre el motivo principal de tu calificación?' "
            "Sé breve, amigable y profesional."
        )
        
        headers = {
            'Authorization': f'Bearer {DATABRICKS_TOKEN}',
            'Content-Type': 'application/json'
        }

        # Payload para el endpoint de Databricks (formato OpenAI compatible)
        payload = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message } # El mensaje del usuario es su calificación/respuesta
            ],
            # "model": LLAMA_MODEL_NAME, # El campo 'model' puede o no ser necesario dependiendo de cómo esté configurado tu endpoint.
                                      # Si el endpoint es específico para un modelo, este campo podría ser ignorado o causar un error si no coincide.
                                      # Lo incluyo basado en tu ejemplo, pero prueba quitarlo si da problemas.
            "temperature": 0.7,
            "max_tokens": 150, # Ajustar según la longitud esperada de la respuesta del bot
            # "stop": ["</end>"] # Opcional, si tu modelo usa secuencias de parada específicas
        }
        
        # Si tu endpoint es específico para "databricks-llama-4-maverick",
        # es posible que no necesites el campo "model" en el payload.
        # Si lo requiere, asegúrate que LLAMA_MODEL_NAME sea el correcto.
        # Por ahora, lo dejamos fuera para probar si el endpoint lo infiere.
        # Si da error, podemos añadirlo: payload["model"] = LLAMA_MODEL_NAME

        print(f"Enviando payload al endpoint de Databricks: {json.dumps(payload, indent=2)}")
        
        response = requests.post(DATABRICKS_ENDPOINT_URL, headers=headers, json=payload)
        response.raise_for_status() # Esto lanzará un error HTTP si la respuesta no es 2xx

        response_data = response.json()
        print(f"Respuesta completa del endpoint: {json.dumps(response_data, indent=2)}")

        # La estructura de la respuesta puede variar ligeramente entre modelos/endpoints
        # Comúnmente es response_data['choices'][0]['message']['content']
        if 'choices' in response_data and \
           len(response_data['choices']) > 0 and \
           'message' in response_data['choices'][0] and \
           'content' in response_data['choices'][0]['message']:
            bot_reply = response_data['choices'][0]['message']['content']
        else:
            # Fallback o manejo de estructura de respuesta inesperada
            print("Advertencia: Estructura de respuesta inesperada del modelo Llama.")
            bot_reply = "Gracias. ¿Hay algo más en lo que pueda ayudarte?" # Respuesta genérica

        print(f"Respuesta generada por el bot (Llama): '{bot_reply}'")
        return jsonify({"reply": bot_reply})

    except requests.exceptions.HTTPError as http_err:
        error_message = f"Error HTTP al contactar el servicio de IA: {http_err}. Respuesta: {response.text}"
        print(error_message)
        return jsonify({"error": "Hubo un problema de comunicación con el servicio de IA."}), 500
    except Exception as e:
        error_message = str(e)
        print(f"Error crítico en /chat al procesar con Databricks Llama: {error_message}")
        return jsonify({"error": f"Error interno al procesar tu solicitud: {error_message}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000)) # Ajusta el puerto si es necesario (e.g., 8080)
    is_debug_mode = os.getenv("FLASK_ENV", "production").lower() == "development"
    
    print(f"Iniciando servidor Flask en host 0.0.0.0 puerto {port}, debug={is_debug_mode}")
    app.run(host='0.0.0.0', port=port, debug=is_debug_mode)
    # En producción, es recomendable no usar debug=True por razones de seguridad.