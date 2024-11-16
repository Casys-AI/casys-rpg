let currentChapter = 1;
let isStreaming = false;
let stopStreaming = false;
let scrollSpeed = 200; // Vitesse initiale pour 200 mots par minute

const messagesContainer = document.getElementById('messages');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const skipBtn = document.getElementById('skip-btn');

function addMessage(content, isNarrator = true) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isNarrator ? 'narrator-message' : 'user-message'}`;
    messageDiv.innerHTML = `<strong>${isNarrator ? 'Narrateur' : 'Vous'} :</strong> ${marked.parse(content)}`;
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight; // Assure le scroll vers le bas
}

async function streamText(text) {
    isStreaming = true;
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message narrator-message';
    messagesContainer.appendChild(messageDiv);

    let displayedText = '';
    messageDiv.innerHTML = `<strong>Narrateur :</strong> `;

    const words = text.split(' '); // Séparer le texte en mots

    for (let i = 0; i < words.length; i++) {
        if (stopStreaming) {
            displayedText = text;
            messageDiv.innerHTML = `<strong>Narrateur :</strong> ` + marked.parse(displayedText);
            break;
        }
        if (displayedText.length > 0) {
            displayedText += ' ';
        }
        displayedText += words[i];
        messageDiv.innerHTML = `<strong>Narrateur :</strong> ` + marked.parse(displayedText);
        messagesContainer.scrollTop = messagesContainer.scrollHeight; // Scroll vers le bas
        await new Promise(resolve => setTimeout(resolve, scrollSpeed));
    }

    isStreaming = false;
    stopStreaming = false;
    messagesContainer.scrollTop = messagesContainer.scrollHeight; // Assure le scroll vers le bas
}


async function getChapter(chapter, skip = false) {
    try {
        const response = await fetch(`/api/chapter/${chapter}`);
        if (!response.ok) return false;

        const data = await response.json();

        if (skip) {
            addMessage(data.content);
        } else {
            await streamText(data.content);
        }

        return true;
    } catch (error) {
        console.error('Error:', error);
        return false;
    }
}

skipBtn.addEventListener('click', async () => {
    if (isStreaming) {
        stopStreaming = true;
        skipBtn.textContent = 'Suivant';
    } else if (skipBtn.textContent === 'Suivant') {
        currentChapter++;
        skipBtn.textContent = 'Passer';
        await getChapter(currentChapter);
    } else {
        await getChapter(currentChapter, true);
        skipBtn.textContent = 'Suivant';
    }
});

async function sendMessage() {
    const message = userInput.value.trim();
    if (message) {
        addMessage(message, false);
        userInput.value = '';

        if (message.toLowerCase() === 'commencer') {
            currentChapter = 1;
            messagesContainer.innerHTML = '';
            await getChapter(currentChapter);
        }
    }
}

userInput.addEventListener('keydown', function(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
});

sendBtn.addEventListener('click', sendMessage);

// Écouteurs d'événements pour accélérer l'affichage des mots avec la barre d'espace
document.addEventListener('keydown', function(event) {
    if (event.code === 'Space') {
        scrollSpeed = 50; // Accélère l'affichage à 800 mots par minute
    }
});

document.addEventListener('keyup', function(event) {
    if (event.code === 'Space') {
        scrollSpeed = 200; // Réinitialise la vitesse à 200 mots par minute
    }
});
