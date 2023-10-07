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
const myForm = document.getElementById('myForm');
const userInput = document.getElementById('message');
const image = document.getElementById('image');


myForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const userMessage = userInput.value;
    appendMessage(userMessage);

    const imageFile = image.files[0];
    if (imageFile) {
        const reader = new FileReader();
        reader.onload = (event) => {
            const imageSrc = event.target.result;
            appendImage(imageSrc);
        };
        reader.readAsDataURL(imageFile);
    }
    HTMLFormElement.prototype.submit.call(myForm);
});

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


// bot.forEach(elem => {
//     const message = elem.textContent;
//     const image = document.createElement("img");
//     //image.src = "../static/assets/volume.png";
//     image.width = 
//     image.alt = "Speaker Icon";
//     elem.innerHTML = message;
//     elem.appendChild(image);
// });

const voice = document.getElementsByClassName('speaker');

function speak(text) {
    const bott = document.getElementsByClassName('bot');
    const utterance = new SpeechSynthesisUtterance(text);
    speechSynthesis.speak(utterance);
}

window.onload = function() {
    const listItems = document.querySelectorAll('.bot');
    listItems.forEach(function(item) {
        const button = document.createElement('button');
        button.style.backgroundColor = 'transparent';
        button.innerHTML = '<span class="speaker"><img src="../static/assets/volume.png" width="25px" ></span>';
        button.addEventListener('click', function() {
            speak(item.textContent);
        });
        item.appendChild(button);
    });
};