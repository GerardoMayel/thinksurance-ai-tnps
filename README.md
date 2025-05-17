# Chatbot Flask con Gemini y Databricks Endpoint

Este proyecto es una aplicación web Flask simple que implementa un chatbot. El chatbot puede utilizar el API de Gemini de Google o un endpoint de modelo desplegado en Databricks para generar respuestas.

## Características

- Interfaz de chat web simple.
- Configuración para usar el API de Gemini.
- Configuración para usar un endpoint de modelo de Databricks.
- Posibilidad de cambiar entre los modelos de lenguaje.
- Estructura de proyecto lista para CI/CD con GitHub Actions y Azure DevOps.

## Estructura del Proyecto

.
├── app.py # Lógica principal de la aplicación Flask
├── config.py # Configuración de la aplicación (API keys, endpoints)
├── requirements.txt # Dependencias de Python
├── .env.example # Ejemplo de archivo de variables de entorno
├── static/ # Archivos estáticos (CSS, JS, imágenes)
│ └── style.css
├── templates/ # Plantillas HTML
│ └── index.html
├── .gitignore # Archivos a ignorar por Git
└── README.md # Este archivo

## Prerrequisitos

- Python 3.8 o superior
- pip (manejador de paquetes de Python)
- Una cuenta de Google con acceso al API de Gemini y una clave API.
- (Opcional) Un modelo de lenguaje desplegado como un endpoint en Databricks y su URL/token de acceso.

## Configuración

1.  **Clonar el repositorio:**

    ```bash
    git clone <URL_DEL_REPOSITORIO>
    cd <NOMBRE_DEL_REPOSITORIO>
    ```

2.  **Crear y activar un entorno virtual:**

    ```bash
    python -m venv venv
    # En Windows
    venv\Scripts\activate
    # En macOS/Linux
    source venv/bin/activate
    ```

3.  **Instalar dependencias:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Configurar variables de entorno:**
    Crea un archivo `.env` en la raíz del proyecto, basándote en `.env.example`.
    ```
    GEMINI_API_KEY="TU_API_KEY_DE_GEMINI"
    DATABRICKS_ENDPOINT_URL="URL_DE_TU_ENDPOINT_DE_DATABRICKS"
    DATABRICKS_API_TOKEN="TU_TOKEN_DE_DATABRICKS" # Si es necesario
    # Especifica el modelo a usar: "gemini" o "databricks"
    ACTIVE_MODEL="gemini"
    ```
    **Nota:** Nunca subas tu archivo `.env` con claves reales a GitHub. Asegúrate de que `.env` esté en tu `.gitignore`.

## Uso

1.  **Ejecutar la aplicación Flask:**

    ```bash
    flask run
    ```

    O, para un modo de desarrollo más detallado:

    ```bash
    export FLASK_APP=app.py
    export FLASK_ENV=development
    flask run
    ```

2.  Abre tu navegador web y ve a `http://127.0.0.1:5000/`.

## Cambiar el Modelo de Lenguaje

Puedes cambiar el modelo de lenguaje que utiliza el chatbot modificando la variable `ACTIVE_MODEL` en tu archivo `.env` a `"gemini"` o `"databricks"` y reiniciando la aplicación Flask.

## Despliegue

### Azure DevOps

1.  Sube tu código a un repositorio de Azure Repos (o GitHub).
2.  Crea un pipeline en Azure Pipelines.
3.  Configura el pipeline para construir y desplegar tu aplicación Flask. Puedes usar Azure App Service, Azure Kubernetes Service (AKS), o Databricks (usando trabajos de Databricks para ejecutar la app si es apropiado para tu caso de uso).
4.  Asegúrate de configurar las variables de entorno (API keys, endpoints) de forma segura en la configuración de tu pipeline o servicio de Azure.

### Databricks

Si deseas que el _chatbot en sí mismo_ se ejecute _dentro_ de Databricks (por ejemplo, como un servicio accesible a través de un proxy o si interactúa profundamente con datos en Databricks), puedes considerar:

1.  **Databricks Model Serving:** Si tu "chatbot" es principalmente un modelo, puedes usar Model Serving. La interfaz Flask actuaría como un frontend para este servicio.
2.  **Ejecutar Flask en un clúster de Databricks:** Esto es menos común para aplicaciones web orientadas al usuario, pero posible para servicios internos. Necesitarías configurar el clúster para exponer el puerto de Flask.

## Contribuir

Las contribuciones son bienvenidas. Por favor, abre un issue o un pull request.

## Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles (no incluido en esta generación básica).
