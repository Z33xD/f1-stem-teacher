const chatWindow = document.getElementById('chat-window');
const input = document.getElementById('user-input');

function addMessage(text, className, isBot = false) {
    // Hide placeholder if it's visible
    const placeholder = document.getElementById('chat-placeholder');
    if (placeholder) {
        placeholder.style.display = 'none';
    }

    const wrapper = document.createElement('div');
    wrapper.className = 'message-wrapper ' + (isBot ? 'bot' : 'user');

    if (isBot) {
        const avatar = document.createElement('img');
        avatar.className = 'bot-avatar';
        avatar.src = 'https://i.pinimg.com/236x/9e/c4/a5/9ec4a54f57a449e2442dee76f35109d5.jpg';
        avatar.alt = 'Bot Avatar';
        wrapper.appendChild(avatar);
    }

    const msg = document.createElement('div');
    msg.className = 'message ' + (isBot ? 'bot-message' : 'user-message');
    if (isBot) {
        msg.innerHTML = DOMPurify.sanitize(marked.parse(text));
    } else {
        msg.textContent = text;
    }

    wrapper.appendChild(msg);
    chatWindow.appendChild(wrapper);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

// Typing effect
let typingIndicator;

function showTypingIndicator() {
    typingIndicator = document.createElement('div');
    typingIndicator.className = 'message-wrapper bot';
    typingIndicator.innerHTML = `
        <img class="bot-avatar" src="https://i.pinimg.com/236x/9e/c4/a5/9ec4a54f57a449e2442dee76f35109d5.jpg" alt="Bot Avatar">
        <div class="typing-indicator">
            <span></span><span></span><span></span>
        </div>
    `;
    chatWindow.appendChild(typingIndicator);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

function removeTypingIndicator() {
    if (typingIndicator && typingIndicator.parentNode) {
        typingIndicator.parentNode.removeChild(typingIndicator);
    }
}

// Sending a message
async function sendMessage() {
    const message = input.value.trim();
    if (!message) return;

    addMessage(message, 'user', false);
    input.value = "";

    showTypingIndicator();

    try {
        const formData = new FormData();
        formData.append('message', message);

        const res = await fetch('/chatbot/chat/', {
            method: 'POST',
            body: formData
        });

        removeTypingIndicator();

        if (!res.ok) {
            throw new Error('Network response was not ok');
        }

        const data = await res.json();
        addMessage(data.response, 'bot', true);
    } catch (err) {
        removeTypingIndicator();
        addMessage("Error connecting to server. Please try again.", 'bot', true);
        console.error('Error:', err);
    }
}

function handleKey(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}

// Function to save notes to localStorage
function saveNotes() {
    const notesContent = document.getElementById('noteArea').innerHTML;
    localStorage.setItem('userNotes', notesContent);
}

// Function to load notes from localStorage
function loadNotes() {
    const savedNotes = localStorage.getItem('userNotes');
    if (savedNotes) {
        document.getElementById('noteArea').innerHTML = savedNotes;
    }
}

// Paste image support
document.getElementById('noteArea').addEventListener('paste', function (e) {
    const items = e.clipboardData.items;
    let imageFound = false;

    for (let i = 0; i < items.length; i++) {
        if (items[i].type.indexOf("image") !== -1) {
            imageFound = true;
            const blob = items[i].getAsFile();
            const reader = new FileReader();
            reader.onload = function (event) {
                const img = document.createElement("img");
                img.src = event.target.result;
                img.style.maxWidth = "100%";
                document.getElementById('noteArea').appendChild(img);
            };
            reader.readAsDataURL(blob);
        }
    }

    // Only prevent default if an image is found
    if (imageFound) {
        e.preventDefault();
    }
});

// Add event listener to save notes whenever there's an input
document.getElementById('noteArea').addEventListener('input', saveNotes);

// Load saved notes on page load
window.addEventListener('load', loadNotes);

// Export Notes to PDF
function exportPDF() {
    const element = document.getElementById('noteArea');
    element.classList.add('print-clean');
    const opt = {
        margin:       0.5,
        filename:     'notes.pdf',
        image:        { type: 'jpeg', quality: 0.98 },
        html2canvas:  { scale: 2 },
        jsPDF:        { unit: 'in', format: 'letter', orientation: 'portrait' }
    };
    html2pdf().set(opt).from(element).save().then(() => {
        element.classList.remove('print-clean');
    });
}

document.addEventListener('DOMContentLoaded', function () {
    const chatbotTab = document.getElementById('chatbot-tab');
    const chatWrapper = document.getElementById('chat-wrapper');
    const tabs = document.querySelectorAll('#sideTabs .nav-link');

    // When chatbot tab is activated on mobile
    chatbotTab.addEventListener('shown.bs.tab', function () {
        chatWrapper.style.display = 'block';
    });

    // Hide chatbot when switching to other tabs on mobile
    tabs.forEach(tab => {
        if (tab !== chatbotTab) {
        tab.addEventListener('shown.bs.tab', () => {
            if (window.innerWidth <= 768) {
            chatWrapper.style.display = 'none';
            }
        });
        }
    });
});

// Desmos
document.addEventListener('DOMContentLoaded', function () {
    const elt = document.getElementById('calculator');
    const calculator = Desmos.GraphingCalculator(elt, {
        expressions: true,
        settingsMenu: false,
        keypad: true
    });
});