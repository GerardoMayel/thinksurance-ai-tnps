# app.py
import os
import requests
import json
from flask import Flask, render_template, request, jsonify, session # Importar session
from dotenv import load_dotenv
import datetime # Para obtener la hora actual

load_dotenv()

app = Flask(__name__)
# Se necesita una clave secreta para usar sesiones en Flask
# Para producción, usa una variable de entorno.
app.secret_key = os.getenv("FLASK_SECRET_KEY", "una_clave_secreta_muy_segura_para_desarrollo_tnps_v2")

# --- Configuración del Endpoint de Databricks Llama (Definida en Código) ---
DATABRICKS_ENDPOINT_URL = "https://adb-3330313079281414.14.azuredatabricks.net/serving-endpoints/databricks-llama-4-maverick/invocations"
DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN")

# Verificar configuración al iniciar
if not DATABRICKS_TOKEN:
    print("ADVERTENCIA: La variable de entorno DATABRICKS_TOKEN no está configurada.")
else:
    print(f"Endpoint de Databricks Llama: '{DATABRICKS_ENDPOINT_URL}' (en código).")
    print("Token de Databricks: Cargado desde variable de entorno.")

def get_time_based_greeting_intro():
    """Retorna una introducción para el saludo basada en la hora actual.
       Considera la zona horaria del servidor donde se ejecuta la app.
    """
    # Si tu servidor está en UTC y quieres la hora de México Central, necesitarías manejar zonas horarias.
    # Por simplicidad, esto usa la hora local del servidor.
    # from zoneinfo import ZoneInfo # Python 3.9+
    # now = datetime.datetime.now(ZoneInfo("America/Mexico_City"))
    now = datetime.datetime.now() # Hora local del servidor
    hour = now.hour
    
    if 5 <= hour < 12:
        return "Buenos días."
    elif 12 <= hour < 19: # Ajustado para tardes hasta las 7 PM
        return "Buenas tardes."
    else:
        return "Buenas noches."

def call_llama_model(system_prompt_content, user_prompt_content):
    """
    Función helper para llamar al modelo Llama en Databricks.
    """
    if not DATABRICKS_TOKEN:
        # Idealmente, esto debería prevenir que la app inicie si el token es vital.
        # O manejarlo más elegantemente en los endpoints.
        raise ValueError("DATABRICKS_TOKEN no está configurado en el servidor.")

    headers = {
        'Authorization': f'Bearer {DATABRICKS_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    messages = []
    if system_prompt_content:
        messages.append({"role": "system", "content": system_prompt_content})
    
    # El historial de chat se maneja a través del prompt del sistema que se reconstruye
    # o se podría pasar explícitamente si se refina la lógica de sesión.
    # Por ahora, el system_prompt lleva el contexto necesario para cada estado.

    if user_prompt_content: # El mensaje actual del usuario
        messages.append({"role": "user", "content": user_prompt_content})

    payload = {
        "messages": messages,
        "temperature": 0.7, 
        "max_tokens": 200  # Ajustar para la longitud de respuesta esperada
    }

    print(f"Payload enviado a Llama: {json.dumps(payload, indent=2)}")
    response = requests.post(DATABRICKS_ENDPOINT_URL, headers=headers, json=payload)
    response.raise_for_status() # Lanza HTTPError para respuestas 4xx/5xx
    response_data = response.json()
    print(f"Respuesta de Llama: {json.dumps(response_data, indent=2)}")

    # Extracción robusta de la respuesta del modelo
    if 'choices' in response_data and \
       len(response_data['choices']) > 0 and \
       'message' in response_data['choices'][0] and \
       'content' in response_data['choices'][0]['message']:
        return response_data['choices'][0]['message']['content']
    
    # Fallbacks para otras estructuras de respuesta comunes
    if 'text' in response_data: return response_data['text']
    if 'generated_text' in response_data: return response_data['generated_text']
    if 'predictions' in response_data and isinstance(response_data['predictions'], list) and len(response_data['predictions']) > 0:
        first_pred = response_data['predictions'][0]
        if isinstance(first_pred, str): return first_pred
        if isinstance(first_pred, dict):
            if 'content' in first_pred: return first_pred['content']
            if 'text' in first_pred: return first_pred['text']
    
    # Si no se encuentra una respuesta válida en los formatos esperados
    raise ValueError(f"Estructura de respuesta inesperada o vacía del modelo Llama: {response_data}")


@app.route('/')
def index_route(): # Renombrado para evitar conflicto con la función index
    """
    Ruta principal que renderiza la interfaz del chat.
    Limpia la sesión para un nuevo inicio de encuesta.
    """
    session.clear() 
    return render_template('index.html')

@app.route('/initialize_chat', methods=['GET'])
def initialize_chat():
    """
    Genera el primer mensaje del bot usando el saludo basado en la hora
    y establece el estado inicial de la conversación.
    """
    session.clear() 
    session['chat_history'] = [] 
    
    time_greeting = get_time_based_greeting_intro() 
    
    system_prompt = (
        f"{time_greeting} Eres un asistente virtual de Zurich Santander. "
        "Tu primera tarea es informar al cliente que recientemente ha recibido un servicio o producto de Zurich Santander. "
        "Luego, pregúntale: 'Para ayudarnos a mejorar, ¿podría decirnos en una escala del 0 al 10 " # Escala 0-10
        "si nos recomendaría con un amigo, familiar o colega?'"
    )
    try:
        bot_greeting = call_llama_model(system_prompt, None) # Sin input de usuario para el primer mensaje
        session['chat_history'].append({"role": "assistant", "content": bot_greeting})
        session['chat_state'] = 'awaiting_rating' # Estado inicial
        print(f"Chat inicializado. Saludo: '{bot_greeting}'. Estado: {session['chat_state']}")
        return jsonify({"reply": bot_greeting})
    except Exception as e:
        print(f"Error crítico al inicializar chat con Llama: {e}")
        # Devolver un error JSON al frontend
        return jsonify({"error": "No se pudo iniciar la conversación con el asistente. Por favor, intente recargar la página."}), 500


@app.route('/chat', methods=['POST'])
def chat_endpoint():
    """
    Maneja los mensajes del usuario y la lógica de la conversación TNPS,
    avanzando por los estados: awaiting_rating, awaiting_reason, completed.
    """
    print(f"\n--- Solicitud a /chat --- Estado de sesión actual: {session.get('chat_state')}")
    user_message = request.json.get('message', '').strip()
    if not user_message:
        return jsonify({"error": "Mensaje vacío."}), 400

    current_state = session.get('chat_state', 'awaiting_rating') 
    chat_history = session.get('chat_history', [])
    chat_history.append({"role": "user", "content": user_message}) # Añadir mensaje actual del usuario al historial

    bot_reply = "Lo siento, ha ocurrido un error procesando tu solicitud. Intenta de nuevo." # Default error reply

    try:
        time_greeting_context = get_time_based_greeting_intro() # Para mantener consistencia en el tono

        if current_state == 'awaiting_rating':
            system_prompt = (
                f"{time_greeting_context} Eres un asistente virtual de Zurich Santander. El usuario está respondiendo a la pregunta sobre su "
                "calificación de recomendación (0-10). Su respuesta anterior fue la pregunta de calificación y ahora el usuario ha respondido con el texto que se te proporciona. "
                "Analiza la respuesta del usuario. Si la respuesta es una calificación numérica válida entre 0 y 10 (incluidos), "
                "agradécele por la calificación (puedes mencionar la calificación dada si lo deseas) y luego pregúntale: "
                "'Gracias por tu calificación. ¿Podrías contarnos un poco más sobre el motivo principal de tu calificación?'. "
                "Si la respuesta NO parece ser una calificación numérica válida (ej. es texto no numérico, una queja, o un número fuera de rango 0-10), "
                "amablemente reitera la pregunta original: 'Entiendo. Para poder continuar, ¿podrías proporcionarme "
                "tu calificación en una escala del 0 al 10, por favor?' "
                "IMPORTANTE: Antepón '[VALID_RATING]' a tu respuesta si la calificación fue válida y procedes a pedir el motivo, o '[INVALID_RATING]' si la calificación no fue válida y estás repitiendo la pregunta."
            )
            full_response = call_llama_model(system_prompt, user_message) # user_message es la respuesta del usuario a la calificación

            if full_response.startswith('[VALID_RATING]'):
                bot_reply = full_response.replace('[VALID_RATING]', '').strip()
                session['chat_state'] = 'awaiting_reason'
                print(f"Estado cambiado a: {session['chat_state']}")
            elif full_response.startswith('[INVALID_RATING]'):
                bot_reply = full_response.replace('[INVALID_RATING]', '').strip()
                # El estado sigue siendo 'awaiting_rating'
                print(f"Calificación inválida. Estado se mantiene: {session['chat_state']}")
            else: 
                # Si el LLM no usa los prefijos, es un comportamiento inesperado o un prompt a mejorar.
                print("Advertencia: El LLM no usó los prefijos [VALID_RATING] o [INVALID_RATING].")
                bot_reply = full_response 
                # Como fallback, si el bot ya pregunta por el motivo, asumimos que la calificación fue válida.
                if "motivo" in bot_reply.lower() or "razón" in bot_reply.lower() or "cuéntanos más" in bot_reply.lower():
                     session['chat_state'] = 'awaiting_reason'
                     print(f"Detectada pregunta por motivo. Estado cambiado a: {session['chat_state']}")


        elif current_state == 'awaiting_reason':
            system_prompt = (
                f"{time_greeting_context} Eres un asistente virtual de Zurich Santander. El cliente previamente dio una calificación y ahora está "
                "proporcionando el motivo de su calificación (el mensaje actual del usuario). "
                "Agradécele por su feedback detallado y finaliza la conversación amablemente. Por ejemplo: "
                "'Muchas gracias por tus comentarios, los tendremos muy en cuenta para mejorar nuestros servicios. "
                "¡Que tengas un excelente día!' No hagas más preguntas."
            )
            bot_reply = call_llama_model(system_prompt, user_message)
            session['chat_state'] = 'completed'
            print(f"Estado cambiado a: {session['chat_state']}")

        elif current_state == 'completed':
            system_prompt = (
                f"{time_greeting_context} Eres un asistente virtual de Zurich Santander. La encuesta TNPS ya ha finalizado. "
                "El usuario ha enviado un mensaje adicional después de completar la encuesta. "
                "Responde amablemente que la encuesta ha concluido y que si tiene otras consultas, "
                "puede contactar los canales habituales de Zurich Santander. No intentes reabrir la encuesta."
            )
            bot_reply = call_llama_model(system_prompt, user_message)
            print(f"Chat en estado 'completed'. Respondiendo a mensaje adicional.")
        
        chat_history.append({"role": "assistant", "content": bot_reply})
        session['chat_history'] = chat_history # Actualizar historial en sesión
        print(f"Respuesta del bot: '{bot_reply}'")

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
    port = int(os.environ.get('PORT', 8000)) # Ajusta el puerto si es necesario
    # Para desarrollo, FLASK_ENV=development habilita el modo debug.
    # Para producción, asegúrate de que FLASK_ENV=production o no esté definido.
    is_debug_mode = os.getenv("FLASK_ENV", "production").lower() == "development"
    
    print(f"Iniciando servidor Flask en host 0.0.0.0 puerto {port}, debug={is_debug_mode}")
    app.run(host='0.0.0.0', port=port, debug=is_debug_mode)
