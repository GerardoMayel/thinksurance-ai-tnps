// static/script.js
document.addEventListener('DOMContentLoaded', () => {
    const messageForm = document.getElementById('message-form');
    const messageInput = document.getElementById('message-input');
    const chatBox = document.getElementById('chat-box');
    const sendButton = document.getElementById('send-button');
    const statusIndicator = document.getElementById('status-indicator');

    const botAvatarSvg = `
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-full h-full">
            <path d="M12 2C6.486 2 2 6.486 2 12s4.486 10 10 10 10-4.486 10-10S17.514 2 12 2zm0 18c-4.411 0-8-3.589-8-8s3.589-8 8-8 8 3.589 8 8-3.589 8-8 8z"/>
            <path d="M12 17c1.654 0 3-1.346 3-3H9c0 1.654 1.346 3 3 3zm-3.5-5c.828 0 1.5-.672 1.5-1.5S9.328 9 8.5 9 7 9.672 7 10.5 7.672 12 8.5 12zm7 0c.828 0 1.5-.672 1.5-1.5S16.328 9 15.5 9s-1.5.672-1.5 1.5.672 1.5 1.5 1.5z"/>
            <path d="M12 6c-1.303 0-2.406.836-2.818 2H14.82c-.412-1.164-1.515-2-2.82-2z"/>
        </svg>
    `;
    const userAvatarSvg = `
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-full h-full">
          <path fill-rule="evenodd" d="M18.685 19.097A9.723 9.723 0 0021.75 12c0-5.385-4.365-9.75-9.75-9.75S2.25 6.615 2.25 12a9.723 9.723 0 003.065 7.097A9.716 9.716 0 0012 21.75a9.716 9.716 0 006.685-2.653zm-12.54-1.285A7.486 7.486 0 0112 15a7.486 7.486 0 015.855 2.812A8.224 8.224 0 0112 20.25a8.224 8.224 0 01-5.855-2.438zM15.75 9a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z" clip-rule="evenodd" />
        </svg>
    `;

    function createAvatarElement(sender) {
        const avatarContainer = document.createElement('div');
        avatarContainer.classList.add('avatar', 'rounded-full', 'w-8', 'h-8', 'flex', 'items-center', 'justify-center', 'text-white', 'font-semibold', 'flex-shrink-0', 'shadow-md', 'overflow-hidden');
        if (sender === 'user') {
            avatarContainer.classList.add('bg-blue-500');
            avatarContainer.innerHTML = userAvatarSvg;
        } else { 
            avatarContainer.classList.add('bg-sky-500');
            avatarContainer.innerHTML = botAvatarSvg;
        }
        return avatarContainer;
    }

    // Función para efecto de máquina de escribir
    function typeWriterEffect(element, text, speed = 30) { // speed en milisegundos por caracter
        let i = 0;
        element.textContent = ""; // Limpiar contenido previo
        
        function type() {
            if (i < text.length) {
                element.textContent += text.charAt(i);
                i++;
                chatBox.scrollTop = chatBox.scrollHeight; // Mantener scroll abajo mientras escribe
                setTimeout(type, speed);
            } else {
                // Opcional: llamar a una función callback cuando termine de escribir
            }
        }
        type();
    }

    function addMessageToChatbox(message, sender) {
        const messageWrapper = document.createElement('div');
        messageWrapper.classList.add('message', sender === 'user' ? 'user-message' : 'bot-message', 'flex', 'items-end', 'mb-2');
        
        if (sender === 'user') {
            messageWrapper.classList.add('justify-end');
        }

        const messageContent = document.createElement('div');
        messageContent.classList.add('flex', 'items-end', 'max-w-md', 'md:max-w-lg');

        const avatarElement = createAvatarElement(sender);

        const paragraph = document.createElement('p');
        // Para respetar saltos de línea y espacios múltiples del texto del bot:
        paragraph.style.whiteSpace = "pre-wrap"; 
        paragraph.classList.add('p-3', 'rounded-lg', 'shadow-md', 'mx-2');
        
        if (sender === 'user') {
            paragraph.textContent = message; // Mensajes del usuario aparecen de inmediato
            paragraph.classList.add('bg-blue-600', 'text-white');
            messageContent.appendChild(paragraph); 
            messageContent.appendChild(avatarElement); 
        } else { // Bot
            // No establecer texto aquí, lo hará el efecto de máquina de escribir
            paragraph.classList.add('bg-sky-600', 'text-white');
            messageContent.appendChild(avatarElement); 
            messageContent.appendChild(paragraph); 
            typeWriterEffect(paragraph, message); // Aplicar efecto al mensaje del bot
        }
        
        messageWrapper.appendChild(messageContent);
        chatBox.appendChild(messageWrapper);
        chatBox.scrollTop = chatBox.scrollHeight; 
    }

    async function initializeChat() {
        messageInput.disabled = true; // Deshabilitar input hasta que el chat se inicialice
        messageInput.placeholder = "Conectando...";
        statusIndicator.textContent = 'Conectando con el asistente...';
        try {
            const response = await fetch('/initialize_chat', { method: 'GET' });
            if (!response.ok) {
                throw new Error(`Error del servidor al iniciar: ${response.status}`);
            }
            const data = await response.json();
            if (data.reply) {
                addMessageToChatbox(data.reply, 'bot');
            } else if (data.error) {
                addMessageToChatbox(data.error, 'bot');
            }
        } catch (error) {
            console.error('Error al inicializar el chat:', error);
            addMessageToChatbox(`Error al conectar: ${error.message}. Intenta recargar.`, 'bot');
        } finally {
            statusIndicator.textContent = '';
            messageInput.disabled = false; 
            messageInput.placeholder = "Escribe tu respuesta aquí...";
            messageInput.focus();
        }
    }
    
    initializeChat(); 

    messageForm.addEventListener('submit', async (event) => {
        event.preventDefault(); 
        const userMessage = messageInput.value.trim();

        if (userMessage) {
            addMessageToChatbox(userMessage, 'user');
            messageInput.value = ''; 
            sendButton.disabled = true; 
            statusIndicator.textContent = 'Asistente está escribiendo...'; // Mostrar antes de la respuesta del bot

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ message: userMessage }),
                });

                // Ocultar "Asistente está escribiendo..." una vez que se recibe la respuesta (o error)
                statusIndicator.textContent = ''; 

                if (!response.ok) {
                    let errorData;
                    try {
                        errorData = await response.json();
                    } catch (e) {
                        errorData = { error: response.statusText };
                    }
                    throw new Error(errorData.error || `Error del servidor: ${response.status}`);
                }

                const data = await response.json();
                if (data.error) { 
                    addMessageToChatbox(data.error, 'bot');
                } else {
                    addMessageToChatbox(data.reply, 'bot');
                }

            } catch (error) {
                console.error('Error al contactar al bot:', error);
                statusIndicator.textContent = ''; // Asegurarse de limpiar en caso de error también
                addMessageToChatbox(`Error: ${error.message || 'No se pudo obtener respuesta.'}`, 'bot');
            } finally {
                // Habilitar botón de enviar solo si el input vuelve a tener texto (el usuario podría escribir rápido)
                sendButton.disabled = messageInput.value.trim() === ''; 
                messageInput.focus(); 
            }
        }
    });

    messageInput.addEventListener('input', () => {
        sendButton.disabled = messageInput.value.trim() === '';
    });
    // El botón se habilita/deshabilita en initializeChat y después de enviar
    // sendButton.disabled = true; // No es necesario aquí si se maneja en otros puntos
});
