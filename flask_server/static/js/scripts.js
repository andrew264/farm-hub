// Get the select element
const langSelect = document.getElementById('langSelect');

// Add an event listener for when the user selects a language
langSelect.addEventListener('change', () => {
// Get the selected language
const selectedLang = langSelect.value;

// Hide all language elements
const langElems = document.querySelectorAll('.lang');
langElems.forEach(elem => {
elem.style.display = 'none';
});

// Show the selected language element
const selectedElem = document.querySelector(`.lang.${selectedLang}`);
selectedElem.style.display = 'block';
});


// JavaScript code to handle user input and display chat
const chatContainer = document.getElementById('chat');
const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('message');
const  image = document.getElementById('image');


chatForm.addEventListener('submit', (e) => {
e.preventDefault();
const userMessage = userInput.value;
appendMessage('User', userMessage);

const imageFile = image.files[0];
if (imageFile) {
const reader = new FileReader();
reader.onload = (event) => {
const imageSrc = event.target.result;
appendImage('User', imageSrc);
fetchBotResponse(userMessage, imageSrc)
.then(botResponse => {
        appendMessage('Bot', botResponse);
        chatForm.reset(); // Reset the form after the bot response is received
    })
.catch(error => {
    console.error(error);
});
};
reader.readAsDataURL(imageFile);
} else {
fetchBotResponse(userMessage)
.then(botResponse => {
    appendMessage('Bot', botResponse);
    chatForm.reset(); // Reset the form after the bot response is received
})
.catch(error => {
    console.error(error);
});
}
});

function appendMessage(sender, message) {
const messageElement = document.createElement('div');
messageElement.textContent = `${sender}: ${message}`;
chatContainer.appendChild(messageElement);
}

function appendImage(sender, imageSrc) {
const imageElement = document.createElement('img');
imageElement.src = imageSrc;
imageElement.alt = `${sender}'s image`;
imageElement.width = 200;
imageElement.height = 200;
chatContainer.appendChild(imageElement);
}


function fetchBotResponse(userMessage, imageSrc) {
// Send the user's message and image to the server for processing (via AJAX or WebSocket)
// Upon receiving a response from your chatbot, append it to the chat
// You can use AJAX or WebSocket to asynchronously communicate with the server
// and append the bot's response to the chat container.
// Here's a simplified example:

// Assume you have a function fetchBotResponse() that fetches the response from the server
// and returns a Promise that resolves with the bot's response
fetchBotResponseFromServer(userMessage, imageSrc)
.then(botResponse => {
appendMessage('Bot', botResponse);
})
.catch(error => {
console.error(error);
});
}

function fetchBotResponseFromServer(userMessage, imageSrc) {
// Use fetch() or WebSocket to send the user's message and image to the server
// and receive the bot's response
// Here's a simplified example using fetch():
const formData = new FormData();
formData.append('message', userMessage);
if (imageSrc) {
formData.append('image', imageSrc);
}
return fetch('/chatbot', {
method: 'POST',
body: formData
})
.then(response => {
if (!response.ok) {
throw new Error('Failed to fetch bot response');
}
return response.text();
});
}

function startSpeechRecognition() {
    const recognition = new webkitSpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    let timeoutId;

    recognition.onresult = function(event) {
        const speechResult = event.results[event.results.length - 1][0].transcript;
        document.getElementById('message').value = speechResult;
        clearTimeout(timeoutId);
        timeoutId = setTimeout(function() {
            recognition.stop();
            startSpeechRecognition();
        }, 3000);
    };

    recognition.onend = function() {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(function() {
            startSpeechRecognition();
        }, 3000);
    };

    recognition.start();
}