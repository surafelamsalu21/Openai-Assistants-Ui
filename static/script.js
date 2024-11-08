window.onload = function () {
    document.getElementById("user-input").focus();
};

let currentThreadId = null; // Variable to store the current thread ID
let recognizing = false;
let recognition; // Speech recognition object

// Check for Web Speech API support
if ("webkitSpeechRecognition" in window) {
    recognition = new webkitSpeechRecognition();
    recognition.continuous = false; // Stops when user stops speaking
    recognition.interimResults = false; // Display only final results
    recognition.lang = "en-US";

    recognition.onstart = function () {
        recognizing = true;
        document.getElementById("voice-input-btn").innerText = "🛑 Stop Voice Input";
    };

    recognition.onend = function () {
        recognizing = false;
        document.getElementById("voice-input-btn").innerText = "🎤 Start Voice Input";
    };

    recognition.onresult = function (event) {
        const transcript = event.results[0][0].transcript;
        document.getElementById("user-input").value = transcript;
        sendUserInput(currentThreadId, transcript); // Send to chat automatically
    };
} else {
    console.warn("Web Speech API not supported in this browser.");
}

// Start/stop voice recognition
document.getElementById("voice-input-btn").addEventListener("click", function () {
    if (recognizing) {
        recognition.stop();
    } else {
        recognition.start();
    }
});

document.getElementById("new-thread-btn").addEventListener("click", function () {
    fetch("/create_thread")
        .then(response => response.json())
        .then(data => {
            if (data.thread_id) {
                currentThreadId = data.thread_id;
                document.getElementById("messages-container").innerHTML = "";
                document.getElementById("user-input").value = "";
            } else {
                console.error("Error creating thread:", data.error);
            }
        })
        .catch(error => {
            console.error("Error:", error);
        });
});

document.getElementById("send-btn").addEventListener("click", function () {
    const userInput = document.getElementById("user-input").value.trim();
    if (userInput && currentThreadId) {
        sendUserInput(currentThreadId, userInput);
    }
});

document.getElementById("file-input").addEventListener("change", function (event) {
    const file = event.target.files[0];
    if (file) {
        // Show the loader
        const loader = document.createElement('div');
        loader.className = 'loader';
        document.getElementById('chat-container').appendChild(loader);
        
        // Upload the file and remove the loader after the upload is complete
        uploadFile(file).finally(() => {
            loader.remove();
        });
    }
});

document.getElementById("chat-container").addEventListener("dragover", function (event) {
    event.preventDefault();
    event.dataTransfer.dropEffect = "copy";
});

document.getElementById("chat-container").addEventListener("drop", function (event) {
    event.preventDefault();
    const file = event.dataTransfer.files[0];
    if (file) {
        // Display the file type
        alert(`Dropped file type: ${file.type}`);
        
        // Show the loader
        const loader = document.createElement('div');
        loader.className = 'loader';
        document.getElementById('chat-container').appendChild(loader);
        
        // Upload the file and remove the loader after the upload is complete
        uploadFile(file).finally(() => {
            loader.remove();
        });
    }
});

function sendUserInput(threadId, userInput) {
    addToChatHistory("User", userInput);
    document.getElementById("user-input").value = "";

    fetch("/ask", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            input: userInput,
            thread_id: threadId,
            assistant_id: currentAssistantId
        }),
    })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                addToChatHistory("Error", data.error);
            } else {
                addToChatHistory("Assistant", data.response);
            }
        })
        .catch(error => {
            console.error("Error:", error);
            addToChatHistory("Error", "Failed to send message.");
        });
}

function uploadFile(file) {
    const formData = new FormData();
    formData.append("file", file);

    return fetch("/upload_file", {
        method: "POST",
        body: formData,
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            addToChatHistory("Error", data.error);
        } else {
            addToChatHistory("Assistant", data.response);
        }
    })
    .catch(error => {
        console.error("Error uploading file:", error);
        addToChatHistory("Error", "Failed to upload file.");
    });
}

function addToChatHistory(role, message) {
    const messagesContainer = document.getElementById("messages-container");
    const messageElement = document.createElement("div");
    messageElement.className = `chat-message ${role}`;
    messageElement.textContent = `${role}: ${message}`;
    messagesContainer.appendChild(messageElement);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Initialize the app
document.addEventListener("DOMContentLoaded", function () {
    document.getElementById("new-thread-btn").click();
});
