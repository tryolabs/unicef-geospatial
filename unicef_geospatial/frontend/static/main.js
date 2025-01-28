let map;
let messageHistory = [];
let sessionId;

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

function switchTab(tabName) {
  const isChat = tabName === "chat";
  document.getElementById("chat-container").style.display = isChat
    ? "block"
    : "none";
  document.getElementById("chain-of-thought-container").style.display = isChat
    ? "none"
    : "block";
  document
    .querySelectorAll(".tab")
    .forEach((tab, i) =>
      tab.classList.toggle("active", i === (isChat ? 0 : 1))
    );
}

function formatContent(thought) {
  if (typeof thought === "object") {
    return JSON.stringify(thought, null, 2);
  }
  return thought;
}

function displayChainOfThought(thoughts, question) {
  const container = document.getElementById("chain-of-thought-container");

  const elements = [
    // Question header
    Object.assign(document.createElement("div"), {
      className: "thought-question",
      innerHTML: `<strong>Question:</strong> ${question}`,
    }),

    document.createElement("hr"),
    Object.assign(document.createElement("div"), {
      className: "thought-container",
      innerHTML: `
        <div class="thought-step">
          <strong>Initial Thought</strong>
          <pre>${formatContent(thoughts[0])}</pre>
        </div>
        <div class="thought-step">
          ${thoughts
            .slice(1)
            .map(
              (thought, index) => `
              <strong>Step ${index + 1}</strong>
              <pre>${formatContent(thought)}</pre>
              <br>

          `
            )
            .join("")}
        </div>
      `,
    }),
  ];

  // Insert all elements at the top
  elements
    .reverse()
    .forEach((el) => container.insertBefore(el, container.firstChild));
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
        session_id: sessionId,
      }),
    });

    const data = await response.json();
    addMessage(data.response, false, data.is_html, data.html_content);
    displayChainOfThought(data.chain_of_thought, question);
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

window.onload = function () {
  sessionId = crypto.randomUUID();
  initializeMap();
};
