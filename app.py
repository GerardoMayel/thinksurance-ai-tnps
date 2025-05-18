# app.py
import os
from flask import Flask, render_template, request, jsonify # render_template, request, jsonify no se usan aún pero se pueden dejar
from dotenv import load_dotenv
# Intentar importar google.generativeai y manejar el error si no se puede
try:
    import google.generativeai as genai
    google_generativeai_imported = True
    print("Módulo google.generativeai importado exitosamente.")
except ImportError as e:
    google_generativeai_imported = False
    genai = None # Asegurarse de que genai esté definido para las comprobaciones posteriores
    print(f"Error al importar google.generativeai: {e}. La funcionalidad de Gemini no estará disponible.")

# Cargar variables de entorno desde el archivo .env (útil para desarrollo local)
# En Databricks, estas variables se establecerán a través de la configuración de la app/secretos.
load_dotenv()

app = Flask(__name__)

# --- Debug: Imprimir todas las variables de entorno en consola (se mantiene por si es útil) ---
print("="*30)
print("Variables de Entorno Disponibles (Consola):")
for key_env, value_env in os.environ.items(): # Renombrado para evitar conflicto con bucle posterior
    print(f"{key_env}: {value_env}")
print("="*30)
# --- Fin Debug Consola ---

# --- Configuración de Gemini (Simplificada para Debug) ---
# Obtener la clave API de Gemini de la variable de entorno.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

gemini_sdk_configured_message = "Configuración del SDK de Gemini temporalmente deshabilitada para depuración."
gemini_model_instance_message = "Instanciación del modelo de Gemini temporalmente deshabilitada para depuración."

if not google_generativeai_imported:
    gemini_sdk_configured_message = "Módulo google.generativeai no pudo ser importado."
elif GEMINI_API_KEY:
    print(f"GEMINI_API_KEY encontrada en las variables de entorno. Valor: '{GEMINI_API_KEY[:5]}...' (primeros 5 caracteres)")
    # TEMPORALMENTE COMENTADO PARA DEBUG:
    # try:
    #     genai.configure(api_key=GEMINI_API_KEY)
    #     gemini_sdk_configured_message = "SDK de Gemini configurado exitosamente (Llamada a configure() comentada para debug)."
    #     print(gemini_sdk_configured_message)
    # except Exception as e:
    #     error_msg = f"Error al intentar configurar el SDK de Gemini (Llamada a configure() comentada para debug): {e}"
    #     gemini_sdk_configured_message = error_msg
    #     print(error_msg)
    gemini_sdk_configured_message = "Llamada a genai.configure() temporalmente deshabilitada. API Key encontrada."

else:
    warning_msg = "Advertencia: La variable de entorno GEMINI_API_KEY no está configurada o está vacía."
    gemini_sdk_configured_message = warning_msg
    gemini_model_instance_message = "La funcionalidad de Gemini no estará disponible."
    print(warning_msg)
    # print(gemini_model_instance_message) # Ya está implícito

@app.route('/')
def index():
    """
    Ruta principal que muestra información de bienvenida, estado de API y variables de entorno.
    """
    # Recopilar variables de entorno para mostrarlas en HTML
    env_vars_html = "<ul>"
    for key, value in sorted(os.environ.items()): # Ordenadas para mejor visualización
        # Escapar HTML en los valores para seguridad básica si se muestran datos arbitrarios
        # import html
        # env_vars_html += f"<li><strong>{html.escape(key)}:</strong> {html.escape(value)}</li>"
        # Por ahora, sin escapar, asumiendo que las variables de entorno son seguras para este contexto de depuración
        env_vars_html += f"<li><strong>{key}:</strong> {value}</li>"
    env_vars_html += "</ul>"

    # Verificar disponibilidad del modelo Gemini (Simplificado para Debug)
    gemini_model_available = False
    gemini_check_message = "Verificación del modelo de Gemini temporalmente deshabilitada para depuración."
    
    if not google_generativeai_imported:
        gemini_check_message = "Módulo google.generativeai no pudo ser importado."
    elif GEMINI_API_KEY and genai:
        # TEMPORALMENTE COMENTADO PARA DEBUG:
        # try:
        #     genai.get_model('models/gemini-pro') # Intenta obtener un modelo para verificar
        #     gemini_model_available = True
        #     gemini_check_message = "Modelo 'models/gemini-pro' accesible (Llamada a get_model() comentada para debug)."
        # except Exception as e:
        #     gemini_check_message = f"Error al verificar el modelo de Gemini ('models/gemini-pro') (Llamada comentada para debug): {e}"
        #     print(gemini_check_message) # También imprimir en consola para logs
        #     gemini_model_available = False
        gemini_check_message = "Llamada a genai.get_model() temporalmente deshabilitada. API Key encontrada."
            
    api_status_page = "funcionalidad de Gemini parcialmente deshabilitada para depuración"

    # Construir el HTML
    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Chatbot Flask - Estado de Depuración</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f0f2f5; color: #333; }}
            .container {{ background-color: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            h1 {{ color: #1d3557; }}
            h2 {{ color: #457b9d; border-bottom: 2px solid #a8dadc; padding-bottom: 5px; margin-top: 30px;}}
            ul {{ list-style-type: none; padding-left: 0; }}
            li {{ background-color: #f1faee; margin-bottom: 8px; padding: 10px; border-radius: 4px; border-left: 5px solid #a8dadc; word-wrap: break-word; }}
            strong {{ color: #e63946; }}
            .status-message {{ padding:10px; border-radius:4px; margin-bottom:10px; }}
            .info {{ background-color: #e0e0e0; color: #333; }}
            .success {{ background-color: #d4edda; color: #155724; }}
            .warning {{ background-color: #fff3cd; color: #856404; }}
            .error {{ background-color: #f8d7da; color: #721c24; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>¡Hola! Soy tu chatbot Flask. (Modo Depuración)</h1>
            <p>Despliegue inicial exitoso.</p>
            
            <h2>Estado de la API de Gemini (Simplificado para Depuración)</h2>
            <p class="status-message info"><strong>Importación del Módulo google.generativeai:</strong> {'Exitoso' if google_generativeai_imported else 'Fallido (ver consola para detalles)'}</p>
            <p class="status-message info"><strong>Lectura de GEMINI_API_KEY:</strong> {'Encontrada' if GEMINI_API_KEY else 'No encontrada o vacía'}</p>
            <p class="status-message warning"><strong>Configuración del SDK (genai.configure):</strong> {gemini_sdk_configured_message}</p>
            <p class="status-message warning"><strong>Verificación del Modelo (genai.get_model):</strong> {gemini_check_message}</p>
            <p class="status-message info"><strong>Estado General API para la página:</strong> {api_status_page}</p>
            
            <h2>Variables de Entorno Disponibles para la Aplicación</h2>
            {env_vars_html}
        </div>
    </body>
    </html>
    """
    return html_content

# (Más adelante añadiremos la ruta /chat para la lógica del chatbot)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000)) # Mantén el puerto que Databricks espera o tu config local
    is_debug_mode = os.getenv("FLASK_ENV", "production").lower() == "development"
    
    # Es importante que debug=False para producción en Databricks,
    # pero para depuración local, True (o basado en FLASK_ENV) es útil.
    # Flask CLI podría pasar su propio flag de debug.
    # Si FLASK_ENV=development, Flask habilita el modo debug por defecto.
    app.run(host='0.0.0.0', port=port, debug=is_debug_mode)

