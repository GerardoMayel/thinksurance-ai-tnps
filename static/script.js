// static/script.js
document.addEventListener('DOMContentLoaded', () => {
    const messageForm = document.getElementById('message-form');
    const messageInput = document.getElementById('message-input');
    const chatBox = document.getElementById('chat-box');
    const sendButton = document.getElementById('send-button');
    const statusIndicator = document.getElementById('status-indicator');

    // Función para añadir mensajes al chatbox
    function addMessageToChatbox(message, sender) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', sender === 'user' ? 'user-message' : 'bot-message');

        const paragraph = document.createElement('p');
        // Sanitizar el texto para evitar XSS simple. Para producción, usar una librería.
        paragraph.textContent = message; 
        
        // Aplicar clases de Tailwind según el emisor
        if (sender === 'user') {
            paragraph.classList.add('bg-sky-500', 'text-white', 'p-3', 'rounded-lg', 'inline-block', 'max-w-xs', 'md:max-w-md', 'ml-auto');
            messageElement.classList.add('text-right'); // Alinea el contenedor del mensaje a la derecha
        } else {
            paragraph.classList.add('bg-slate-600', 'text-white', 'p-3', 'rounded-lg', 'inline-block', 'max-w-xs', 'md:max-w-md');
        }
        
        messageElement.appendChild(paragraph);
        chatBox.appendChild(messageElement);
        chatBox.scrollTop = chatBox.scrollHeight; // Auto-scroll hacia el último mensaje
    }

    messageForm.addEventListener('submit', async (event) => {
        event.preventDefault(); // Evitar que el formulario recargue la página
        const userMessage = messageInput.value.trim();

        if (userMessage) {
            addMessageToChatbox(userMessage, 'user');
            messageInput.value = ''; // Limpiar el campo de entrada
            sendButton.disabled = true; // Deshabilitar botón mientras se espera respuesta
            statusIndicator.textContent = 'Bot está escribiendo...';

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ message: userMessage }),
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || `Error del servidor: ${response.status}`);
                }

                const data = await response.json();
                addMessageToChatbox(data.reply, 'bot');

            } catch (error) {
                console.error('Error al contactar al bot:', error);
                addMessageToChatbox(`Error: ${error.message || 'No se pudo obtener respuesta.'}`, 'bot');
            } finally {
                sendButton.disabled = false; // Rehabilitar el botón
                statusIndicator.textContent = ''; // Limpiar indicador de estado
                messageInput.focus(); // Devolver el foco al input
            }
        }
    });

    // Habilitar/deshabilitar el botón de enviar basado en si hay texto en el input
    messageInput.addEventListener('input', () => {
        sendButton.disabled = messageInput.value.trim() === '';
    });
    sendButton.disabled = true; // Inicialmente deshabilitado
});
