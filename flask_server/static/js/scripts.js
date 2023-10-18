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
const chatContainer = document.getElementById('chat-container');
const submitButton = document.getElementById('submitButton');
const userInput = document.getElementById('message');
const image = document.getElementById('image');
const socket = io.connect('http://' + location.hostname + ':' + location.port);

submitButton.addEventListener('click', async (e) => {
    e.preventDefault();
    let imageSrc = null;

    const imageFile = image.files[0];
    if (imageFile) {
        imageSrc = await loadImage(imageFile);
        appendImage(imageSrc);
        if (image.files.length > 0) {
            // Clear the selected file
            image.value = '';
        }
    }
    if (userInput.value === '' && imageSrc === null) {
        return;
    }
    const userMessage = userInput.value;
    userInput.value = '';
    submitToSocket(userMessage, imageSrc);

    if (userMessage !== '') {
        appendMessage(userMessage);
    }
    await fetchBotMessage();
});

function submitToSocket(message, image) {
    socket.emit('submit', {message, image});
    console.log('submitted');
}

function loadImage(imageFile) {
    return new Promise((resolve) => {
        const reader = new FileReader();
        reader.onload = (event) => {
            const imageSrc = event.target.result;
            resolve(imageSrc);
        };
        reader.readAsDataURL(imageFile);
    });
}

function appendMessage(message) {
    const messageElement = document.createElement('li');
    messageElement.className = 'user'
    messageElement.innerText = message
    chatContainer.appendChild(messageElement);
}

function appendImage(imageSrc) {
    const imageLi = document.createElement('li');
    imageLi.className = 'user';
    const imageElement = document.createElement('img');
    imageElement.src = imageSrc;
    imageElement.alt = `User image`;
    imageElement.width = 300;
    imageElement.height = 300;
    imageLi.appendChild(imageElement);
    chatContainer.appendChild(imageLi);
}

function createBotMessage() {
    const messageElement = document.createElement('li');
    messageElement.className = 'bot'
    messageElement.innerText = ''
    chatContainer.appendChild(messageElement);
    return messageElement;
}

function fetchBotMessage() {
    const botElement = createBotMessage();

    return new Promise((resolve) => {
        socket.on('content', function (data) {
            botElement.innerText.replaceAll('</s>', '')
            if (data === '//EOS//') {
                resolve();
                socket.off('content');
                return;
            }
            botElement.innerText += data;
            resolve();
        });
    });
}


function startSpeechRecognition() {
    const recognition = new webkitSpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    let timeoutId;

    recognition.onresult = function (event) {
        const speechResult = event.results[event.results.length - 1][0].transcript;
        document.getElementById('message').value = speechResult;
        clearTimeout(timeoutId);
        timeoutId = setTimeout(function () {
            recognition.stop();
            startSpeechRecognition();
        }, 3000);
    };

    recognition.onend = function () {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(function () {
            startSpeechRecognition();
        }, 3000);
    };

    recognition.start();
}


const voice = document.getElementsByClassName('speaker');

function speak(text) {
    const bott = document.getElementsByClassName('bot');
    const utterance = new SpeechSynthesisUtterance(text);
    speechSynthesis.speak(utterance);
}

window.onload = function () {
    const listItems = document.querySelectorAll('.bot');
    listItems.forEach(function (item) {
        const button = document.createElement('button');
        button.style.backgroundColor = 'transparent';
        button.innerHTML = '<span class="speaker"><img src="../static/assets/volume.png" width="25px" ></span>';
        button.addEventListener('click', function () {
            speak(item.textContent);
        });
        item.appendChild(button);
    });
};