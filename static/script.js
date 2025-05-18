// static/script.js
document.addEventListener('DOMContentLoaded', () => {
    const messageForm = document.getElementById('message-form');
    const messageInput = document.getElementById('message-input');
    const chatBox = document.getElementById('chat-box');
    const sendButton = document.getElementById('send-button');
    const statusIndicator = document.getElementById('status-indicator');

    // Placeholder para el avatar del bot (SVG simple)
    // Puedes reemplazar esto con un <img src="url_o_path_a_tu_logo_ZS_o_bot.svg"> si lo tienes en static
    // o una URL completa si es externa (asegúrate de CORS y disponibilidad).
    const botAvatarSvg = `
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-full h-full">
            <path fill-rule="evenodd" d="M7.5 6a4.5 4.5 0 119 0 4.5 4.5 0 01-9 0zM3.751 20.105a8.25 8.25 0 0116.498 0 .75.75 0 01-.437.695A18.683 18.683 0 0112 22.5c-2.786 0-5.433-.608-7.812-1.7a.75.75 0 01-.437-.695z" clip-rule="evenodd" />
        </svg>
    `;
    // Placeholder para el avatar del usuario
    const userAvatarSvg = `
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-full h-full">
          <path fill-rule="evenodd" d="M18.685 19.097A9.723 9.723 0 0021.75 12c0-5.385-4.365-9.75-9.75-9.75S2.25 6.615 2.25 12a9.723 9.723 0 003.065 7.097A9.716 9.716 0 0012 21.75a9.716 9.716 0 006.685-2.653zm-12.54-1.285A7.486 7.486 0 0112 15a7.486 7.486 0 015.855 2.812A8.224 8.224 0 0112 20.25a8.224 8.224 0 01-5.855-2.438zM15.75 9a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z" clip-rule="evenodd" />
        </svg>
    `;


    function createAvatarElement(sender) {
        const avatarContainer = document.createElement('div');
        avatarContainer.classList.add('avatar', 'rounded-full', 'w-8', 'h-8', 'flex', 'items-center', 'justify-center', 'text-white', 'font-semibold', 'flex-shrink-0', 'shadow-md', 'p-1');
        if (sender === 'user') {
            avatarContainer.classList.add('bg-blue-500');
            avatarContainer.innerHTML = userAvatarSvg;
        } else { // Bot
            avatarContainer.classList.add('bg-sky-500');
            // Para el logo ZS, podrías usar un texto "ZS" o un SVG más complejo
            // avatarContainer.textContent = 'ZS'; 
            avatarContainer.innerHTML = botAvatarSvg; // Usando el SVG del bot
        }
        return avatarContainer;
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
        paragraph.classList.add('p-3', 'rounded-lg', 'shadow-md', 'mx-2');
        
        paragraph.textContent = message; 

        if (sender === 'user') {
            paragraph.classList.add('bg-blue-600', 'text-white');
            messageContent.appendChild(paragraph); // Texto primero
            messageContent.appendChild(avatarElement); // Avatar después
        } else { // Bot
            paragraph.classList.add('bg-sky-600', 'text-white');
            messageContent.appendChild(avatarElement); // Avatar primero
            messageContent.appendChild(paragraph); // Texto después
        }
        
        messageWrapper.appendChild(messageContent);
        chatBox.appendChild(messageWrapper);
        chatBox.scrollTop = chatBox.scrollHeight; 
    }

    async function initializeChat() {
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
            messageInput.disabled = false; // Habilitar input después de cargar el primer mensaje
            messageInput.focus();
        }
    }
    
    messageInput.disabled = true; // Deshabilitar input hasta que el chat se inicialice
    initializeChat(); // Iniciar el chat al cargar la página

    messageForm.addEventListener('submit', async (event) => {
        event.preventDefault(); 
        const userMessage = messageInput.value.trim();

        if (userMessage) {
            addMessageToChatbox(userMessage, 'user');
            messageInput.value = ''; 
            sendButton.disabled = true; 
            statusIndicator.textContent = 'Asistente está escribiendo...';

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ message: userMessage }),
                });

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
                addMessageToChatbox(`Error: ${error.message || 'No se pudo obtener respuesta.'}`, 'bot');
            } finally {
                sendButton.disabled = messageInput.value.trim() === ''; // Habilitar solo si hay texto
                statusIndicator.textContent = ''; 
                messageInput.focus(); 
            }
        }
    });

    messageInput.addEventListener('input', () => {
        sendButton.disabled = messageInput.value.trim() === '';
    });
    sendButton.disabled = true; 
});