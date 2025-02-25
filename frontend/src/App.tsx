import { useState, useEffect } from "react";
import MapContainer from "./components/MapContainer.js";
import ChatSection from "./components/ChatSection.js";
import UserGuide from "./components/UserGuide.js";
import { Message } from "./types/Message.js";
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
  const [messageHistory, setMessageHistory] = useState<Message[]>([]);
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
  }, []);

  // Sends user question to the server
  async function askQuestion(question: string): Promise<void> {
    if (!question.trim()) return;

    const question_message = {
      content: question,
      role: "user" as const,
      trace_id: generateUUID(),
      feedback_given: undefined,
    };

    setMessageHistory((prev) => [...prev, question_message]);

    try {
      const body = {
        chat_messages: [...messageHistory, question_message],
        session_id: sessionId,
      };
      console.log(body);
      console.log(JSON.stringify(body));
      const response = await fetch(`${import.meta.env.VITE_BACKEND_URL}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data: {
        response: string;
        is_html: boolean;
        html_content?: string;
        chain_of_thought: string[];
        trace_id: string;
      } = await response.json();

      // Add assistant's reply
      const response_message = {
        content: data.response,
        role: "assistant" as const,
        trace_id: data.trace_id,
      };
      setMessageHistory((prev) => [...prev, response_message]);
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
      const error_message = {
        content: "Sorry, there was an error processing your request.",
        role: "assistant" as const,
        trace_id: generateUUID(),
      };
      setMessageHistory((prev) => [...prev, error_message]);
    }
  }

  function switchTab(tab: "chat" | "thoughts"): void {
    setActiveTab(tab);
  }

  return (
    <div className="app-container">
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
      <UserGuide />
    </div>
  );
}

export default App;
