import { useState, useEffect } from "react";
import MapContainer from "./components/MapContainer.js";
import ChatSection from "./components/ChatSection.js";

function generateUUID(): string {
  // TODO: use an external library to generate a UUID
  return "10000000-1000-4000-8000-100000000000".replace(/[018]/g, (c) =>
    (
      +c ^
      (crypto.getRandomValues(new Uint8Array(1))[0] & (15 >> (+c / 4)))
    ).toString(16)
  );
}

function App() {
  const [messageHistory, setMessageHistory] = useState<string[]>([]);
  const [sessionId, setSessionId] = useState<string>("");
  const [activeTab, setActiveTab] = useState<"chat" | "thoughts">("chat");
  const [chainOfThoughts, setChainOfThoughts] = useState<
    Array<{
      question: string;
      thoughts: string[];
    }>
  >([]);
  const [mapHTML, setMapHTML] = useState<string>("");

  useEffect(() => {
    setSessionId(generateUUID());
    initializeMap();
  }, []);

  // For generating the initial map HTML
  function initializeMap(): void {
    const initialMapHTML = `
      <!DOCTYPE html>
      <html>
        <head>
          <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
          <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
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
    setMapHTML(initialMapHTML);
  }

  // Sends user question to the server
  async function askQuestion(question: string): Promise<void> {
    if (!question.trim()) return;

    setMessageHistory((prev) => [...prev, question]);

    try {
      const response = await fetch(`${import.meta.env.VITE_BACKEND_URL}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          chat_messages: [...messageHistory, question],
          session_id: sessionId,
        }),
      });
      const data: {
        response: string;
        is_html: boolean;
        html_content?: string;
        chain_of_thought: string[];
      } = await response.json();

      // Add assistant's reply
      setMessageHistory((prev) => [...prev, data.response]);

      if (data.is_html && data.html_content) {
        setMapHTML(data.html_content);
      }

      setChainOfThoughts((prev) => [
        {
          question,
          thoughts: data.chain_of_thought,
        },
        ...prev,
      ]);
    } catch (error) {
      console.error(error);
      setMessageHistory((prev) => [
        ...prev,
        "Sorry, there was an error processing your request.",
      ]);
    }
  }

  function switchTab(tab: "chat" | "thoughts"): void {
    setActiveTab(tab);
  }

  return (
    <div className="container">
      <MapContainer mapHTML={mapHTML} />
      <ChatSection
        activeTab={activeTab}
        messageHistory={messageHistory}
        chainOfThoughts={chainOfThoughts}
        switchTab={switchTab}
        askQuestion={askQuestion}
      />
    </div>
  );
}

export default App;
