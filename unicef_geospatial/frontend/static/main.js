let map;
let messageHistory = [];

function initializeMap() {
  const initialMapHTML = `
    <!DOCTYPE html>
    <html>
      <head>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"><\/script>
        <style>
          body { margin: 0; }
          #map { height: 100vh; }
        </style>
      </head>
      <body>
        <div id="map"></div>
        <script>
          const map = L.map('map').setView([20, 0], 2);
          L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
          }).addTo(map);
        <\/script>
      </body>
    </html>
  `;
  updateMap(initialMapHTML);
}

function updateMap(htmlContent) {
  const mapFrame = document.getElementById("map-frame");
  const blob = new Blob([htmlContent], { type: "text/html" });
  mapFrame.src = URL.createObjectURL(blob);
}

function addMessage(content, isUser, isHtml = false, htmlContent = null) {
  const chatContainer = document.getElementById("chat-container");
  const messageDiv = document.createElement("div");
  messageDiv.className = `message ${
    isUser ? "user-message" : "assistant-message"
  }`;
  messageDiv.textContent = content;
  if (isHtml) {
    updateMap(htmlContent);
  }

  messageHistory.push(content);

  chatContainer.appendChild(messageDiv);
  chatContainer.scrollTop = chatContainer.scrollHeight;
}

async function askQuestion() {
  const input = document.getElementById("question-input");
  const question = input.value.trim();

  if (!question) return;

  addMessage(question, true);
  input.value = "";

  try {
    const response = await fetch("/ask", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        chat_messages: messageHistory,
      }),
    });

    const data = await response.json();
    addMessage(data.response, false, data.is_html, data.html_content);
  } catch (error) {
    console.error("Error:", error);
    addMessage("Sorry, there was an error processing your request.", false);
  }
}

// Allow Enter key to submit
document
  .getElementById("question-input")
  .addEventListener("keypress", function (e) {
    if (e.key === "Enter") {
      askQuestion();
    }
  });

// Initialize the map when the page loads
window.onload = initializeMap;
