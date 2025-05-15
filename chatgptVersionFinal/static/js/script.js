document.addEventListener('DOMContentLoaded', function() {
    // Éléments du DOM
    const chatContainer = document.getElementById('chat-container');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');

    // Message d'accueil initial
    addBotMessage("Assistant d'urgence prêt. Posez vos questions sur les catastrophes naturelles.");

    // Fonction pour ajouter un message utilisateur
    function addUserMessage(text) {
        addMessage('Vous', text, 'user');
    }

    // Fonction pour ajouter un message du bot
    function addBotMessage(text) {
        addMessage('Assistant', text, 'bot');
    }

    // Fonction générique pour ajouter un message
    function addMessage(sender, text, type) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', `${type}-message`);
        
        // Formatage spécial pour les messages d'urgence
        if (text.includes('🔴') || text.includes('⚠️')) {
            messageDiv.classList.add('emergency-message');
            messageDiv.innerHTML = `
                <div class="message-header">
                    <strong>${sender}</strong>
                    <span class="emergency-icon">🚨</span>
                </div>
                <div class="message-content">${text}</div>
            `;
        } else {
            messageDiv.innerHTML = `
                <div class="message-header">
                    <strong>${sender}</strong>
                </div>
                <div class="message-content">${text}</div>
            `;
        }

        chatContainer.appendChild(messageDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
        
        // Animation de "typing"
        if (type === 'bot') {
            messageDiv.style.opacity = '0';
            setTimeout(() => {
                messageDiv.style.transition = 'opacity 0.3s ease';
                messageDiv.style.opacity = '1';
            }, 100);
        }
    }

    // Fonction pour envoyer un message
    async function sendMessage() {
        const message = userInput.value.trim();
        if (!message) return;

        addUserMessage(message);
        userInput.value = '';
        userInput.focus();

        // Afficher un indicateur de "typing"
        const typingIndicator = document.createElement('div');
        typingIndicator.classList.add('message', 'bot-message', 'typing');
        typingIndicator.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';
        chatContainer.appendChild(typingIndicator);
        chatContainer.scrollTop = chatContainer.scrollHeight;

        try {
            const response = await fetch('/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message })
            });

            // Retirer l'indicateur de "typing"
            chatContainer.removeChild(typingIndicator);

            const data = await response.json();
            addBotMessage(data.response);
        } catch (error) {
            chatContainer.removeChild(typingIndicator);
            addBotMessage("⚠️ Désolé, une erreur s'est produite. Veuillez réessayer.");
            console.error('Erreur:', error);
        }
    }

    // Gestionnaires d'événements
    sendBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });

    // Focus automatique sur le champ de saisie
    userInput.focus();
});