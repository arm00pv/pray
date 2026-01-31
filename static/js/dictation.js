// Voice-to-Text Dictation Helper
// Handles Web Speech API for any target input/textarea

class DictationHandler {
    constructor() {
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            console.warn('Speech recognition not supported.');
            this.supported = false;
            return;
        }
        this.supported = true;
        this.recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
        this.recognition.continuous = false; // Stop after sentence/pause
        this.recognition.interimResults = false;
        this.isListening = false;
        this.currentBtn = null;
        this.currentInput = null;

        // Default language from HTML lang attribute or 'en'
        this.recognition.lang = document.documentElement.lang || 'en';

        this.recognition.onstart = () => this.handleStart();
        this.recognition.onend = () => this.handleEnd();
        this.recognition.onresult = (e) => this.handleResult(e);
        this.recognition.onerror = (e) => this.handleError(e);
    }

    toggle(btnId, inputId) {
        if (!this.supported) {
            alert("Dictation is not supported in this browser. Try Chrome or Edge.");
            return;
        }

        const btn = document.getElementById(btnId);
        const input = document.getElementById(inputId);

        if (this.isListening) {
            this.recognition.stop();
            return; // onend will clean up
        }

        this.currentBtn = btn;
        this.currentInput = input;
        this.recognition.start();
    }

    handleStart() {
        this.isListening = true;
        if (this.currentBtn) {
            this.currentBtn.classList.add('text-danger', 'fa-beat-fade'); // Add animation class if using FontAwesome, or just style
            this.currentBtn.style.color = 'red';
            this.currentBtn.innerHTML = '🔴'; // Recording icon
        }
    }

    handleEnd() {
        this.isListening = false;
        if (this.currentBtn) {
            this.currentBtn.classList.remove('text-danger', 'fa-beat-fade');
            this.currentBtn.style.color = '';
            this.currentBtn.innerHTML = '🎤'; // Reset icon
        }
        this.currentBtn = null;
        this.currentInput = null;
    }

    handleResult(event) {
        const transcript = event.results[0][0].transcript;
        if (this.currentInput) {
            // Append to existing text with a space
            const currentVal = this.currentInput.value;
            this.currentInput.value = currentVal ? currentVal + " " + transcript : transcript;
        }
    }

    handleError(event) {
        console.error('Speech recognition error', event.error);
        this.handleEnd();
    }
}

// Global instance
const dictation = new DictationHandler();
