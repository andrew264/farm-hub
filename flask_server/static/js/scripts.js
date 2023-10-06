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

