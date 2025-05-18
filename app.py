# app.py
import os
import requests
import json
from flask import Flask, render_template, request, jsonify, session # Importar session
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
# Se necesita una clave secreta para usar sesiones en Flask
app.secret_key = os.getenv("FLASK_SECRET_KEY", "una_clave_secreta_muy_segura_para_desarrollo")

# --- Configuración del Endpoint de Databricks Llama (Definida en Código) ---
DATABRICKS_ENDPOINT_URL = "https://adb-3330313079281414.14.azuredatabricks.net/serving-endpoints/databricks-llama-4-maverick/invocations"
DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN")

# Verificar configuración al iniciar
if not DATABRICKS_TOKEN:
    print("ADVERTENCIA: La variable de entorno DATABRICKS_TOKEN no está configurada.")
else:
    print(f"Endpoint de Databricks Llama: '{DATABRICKS_ENDPOINT_URL}' (en código).")
    print("Token de Databricks: Cargado desde variable de entorno.")

def call_llama_model(system_prompt_content, user_prompt_content, conversation_history=None):
    """
    Función helper para llamar al modelo Llama en Databricks.
    conversation_history es una lista de mensajes previos en formato {"role": "...", "content": "..."}
    """
    if not DATABRICKS_TOKEN:
        raise ValueError("DATABRICKS_TOKEN no está configurado.")

    headers = {
        'Authorization': f'Bearer {DATABRICKS_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    messages = []
    if system_prompt_content:
        messages.append({"role": "system", "content": system_prompt_content})
    
    if conversation_history:
        messages.extend(conversation_history) # Añadir historial si existe

    if user_prompt_content: # El mensaje actual del usuario
        messages.append({"role": "user", "content": user_prompt_content})

    payload = {
        "messages": messages,
        "temperature": 0.7, # Ajustar según se necesite
        "max_tokens": 200  # Ajustar para la longitud de respuesta esperada
    }

    print(f"Payload enviado a Llama: {json.dumps(payload, indent=2)}")
    response = requests.post(DATABRICKS_ENDPOINT_URL, headers=headers, json=payload)
    response.raise_for_status()
    response_data = response.json()
    print(f"Respuesta de Llama: {json.dumps(response_data, indent=2)}")

    if 'choices' in response_data and \
       len(response_data['choices']) > 0 and \
       'message' in response_data['choices'][0] and \
       'content' in response_data['choices'][0]['message']:
        return response_data['choices'][0]['message']['content']
    
    # Fallback para otras estructuras de respuesta comunes
    if 'text' in response_data: return response_data['text']
    if 'generated_text' in response_data: return response_data['generated_text']
    if 'predictions' in response_data and isinstance(response_data['predictions'], list) and len(response_data['predictions']) > 0:
        first_pred = response_data['predictions'][0]
        if isinstance(first_pred, str): return first_pred
        if isinstance(first_pred, dict) and 'content' in first_pred: return first_pred['content']
        if isinstance(first_pred, dict) and 'text' in first_pred: return first_pred['text']

    raise ValueError("Estructura de respuesta inesperada del modelo Llama.")


@app.route('/')
def index_route(): # Renombrado para evitar conflicto con la función index
    """
    Ruta principal que renderiza la interfaz del chat.
    """
    session.clear() # Limpiar sesión al cargar la página principal
    return render_template('index.html')

@app.route('/initialize_chat', methods=['GET'])
def initialize_chat():
    """
    Genera el primer mensaje del bot y establece el estado inicial de la conversación.
    """
    session.clear() # Limpiar cualquier estado previo de sesión
    session['chat_history'] = [] # Inicializar historial de chat
    
    system_prompt = (
        "Eres un asistente virtual de Zurich Santander. Tu primera tarea es saludar al cliente amablemente "
        "e informarle que recientemente ha recibido un servicio o producto de Zurich Santander. "
        "Luego, pregúntale: 'Para ayudarnos a mejorar, ¿podría decirnos en una escala del 0 al 10 "
        "si nos recomendaría con un amigo, familiar o colega?'"
    )
    try:
        bot_greeting = call_llama_model(system_prompt, None) # Sin input de usuario para el primer mensaje
        session['chat_history'].append({"role": "assistant", "content": bot_greeting})
        session['chat_state'] = 'awaiting_rating'
        return jsonify({"reply": bot_greeting})
    except Exception as e:
        print(f"Error al inicializar chat con Llama: {e}")
        return jsonify({"error": "No se pudo iniciar la conversación con el asistente."}), 500


@app.route('/chat', methods=['POST'])
def chat_endpoint():
    """
    Maneja los mensajes del usuario y la lógica de la conversación TNPS.
    """
    print(f"\n--- Solicitud a /chat --- Estado de sesión: {session.get('chat_state')}")
    user_message = request.json.get('message', '').strip()
    if not user_message:
        return jsonify({"error": "Mensaje vacío."}), 400

    current_state = session.get('chat_state', 'awaiting_rating') # Default al inicio si no hay estado
    chat_history = session.get('chat_history', [])
    chat_history.append({"role": "user", "content": user_message}) # Añadir mensaje actual del usuario al historial

    bot_reply = "Lo siento, ha ocurrido un error." # Default error reply

    try:
        if current_state == 'awaiting_rating':
            system_prompt = (
                "Eres un asistente virtual de Zurich Santander. El usuario está respondiendo a la pregunta sobre su "
                "calificación de recomendación (0-10). Su respuesta anterior fue la pregunta de calificación y ahora el usuario ha respondido. "
                "Analiza la respuesta del usuario. Si la respuesta es una calificación numérica válida entre 0 y 10, "
                "agradécele por la calificación (mencionando la calificación dada si es posible) y luego pregúntale: "
                "'Gracias por tu calificación. ¿Podrías contarnos un poco más sobre el motivo principal de tu calificación?'. "
                "Si la respuesta NO parece ser una calificación numérica válida (ej. es texto, una queja, o un número fuera de rango), "
                "amablemente reitera la pregunta original: 'Entiendo. Para poder continuar, ¿podrías proporcionarme "
                "tu calificación en una escala del 0 al 10, por favor?' Indica internamente si la calificación fue válida "
                "anteponiendo '[VALID_RATING]' o '[INVALID_RATING]' a tu respuesta visible para el usuario."
            )
            # Pasamos el historial relevante (última pregunta del bot y respuesta del usuario)
            # O podríamos pasar solo el último mensaje del usuario y el system prompt se encarga del contexto.
            # Para simplificar, el system prompt es bastante descriptivo.
            full_response = call_llama_model(system_prompt, user_message) # El user_message es la respuesta a la calificación

            if full_response.startswith('[VALID_RATING]'):
                bot_reply = full_response.replace('[VALID_RATING]', '').strip()
                session['chat_state'] = 'awaiting_reason'
                session['last_rating'] = user_message # Guardar la calificación (asumiendo que el LLM la validó)
            elif full_response.startswith('[INVALID_RATING]'):
                bot_reply = full_response.replace('[INVALID_RATING]', '').strip()
                # El estado sigue siendo 'awaiting_rating'
            else: # Si el LLM no usó los prefijos, asumimos que es una respuesta directa
                bot_reply = full_response
                # Aquí podríamos intentar una heurística para ver si pasamos al siguiente estado
                # o si el LLM ya hizo la pregunta de seguimiento. Por ahora, si no hay prefijo,
                # dejamos que el LLM guíe y el usuario responda.
                # Si la respuesta del bot contiene "motivo" o "razón", es probable que haya pasado al siguiente estado.
                if "motivo" in bot_reply.lower() or "razón" in bot_reply.lower() or "cuéntanos más" in bot_reply.lower():
                     session['chat_state'] = 'awaiting_reason'


        elif current_state == 'awaiting_reason':
            last_rating = session.get('last_rating', 'esa') # Usar 'esa' si no se guardó la calificación
            system_prompt = (
                f"Eres un asistente virtual de Zurich Santander. El cliente dio una calificación de '{last_rating}' y ahora está "
                "proporcionando el motivo de su calificación. Su comentario es el último mensaje del usuario. "
                "Agradécele por su feedback detallado y finaliza la conversación amablemente. Por ejemplo: "
                "'Muchas gracias por tus comentarios, los tendremos muy en cuenta para mejorar nuestros servicios. "
                "¡Que tengas un buen día!' No hagas más preguntas."
            )
            bot_reply = call_llama_model(system_prompt, user_message)
            session['chat_state'] = 'completed'

        elif current_state == 'completed':
            system_prompt = (
                "Eres un asistente virtual de Zurich Santander. La encuesta TNPS ya ha finalizado. "
                "El usuario ha enviado un mensaje adicional después de completar la encuesta. "
                "Responde amablemente que la encuesta ha concluido y que si tiene otras consultas, "
                "puede contactar los canales habituales de Zurich Santander. No intentes reabrir la encuesta."
            )
            bot_reply = call_llama_model(system_prompt, user_message)
        
        chat_history.append({"role": "assistant", "content": bot_reply})
        session['chat_history'] = chat_history # Actualizar historial en sesión

        return jsonify({"reply": bot_reply})

    except requests.exceptions.HTTPError as http_err:
        error_message = f"Error HTTP: {http_err}. Respuesta: {http_err.response.text if http_err.response else 'No response text'}"
        print(error_message)
        return jsonify({"error": "Hubo un problema de comunicación con el servicio de IA."}), 500
    except ValueError as ve: # Errores de valor, como respuesta inesperada del modelo
        print(f"Error de valor en /chat: {ve}")
        return jsonify({"error": f"Error procesando la respuesta del modelo: {ve}"}), 500
    except Exception as e:
        error_message = str(e)
        print(f"Error crítico en /chat: {error_message}")
        return jsonify({"error": f"Error interno al procesar tu solicitud: {error_message}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    is_debug_mode = os.getenv("FLASK_ENV", "production").lower() == "development"
    print(f"Iniciando servidor Flask en host 0.0.0.0 puerto {port}, debug={is_debug_mode}")
    app.run(host='0.0.0.0', port=port, debug=is_debug_mode)

