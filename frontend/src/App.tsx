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
  const [activeTab, setActiveTab] = useState<"chat" | "tools">("chat");
  const [toolCalls, setToolCalls] = useState<
    Array<{
      question: string;
      toolCalls: string[];
    }>
  >([]);
  const [mapHTML, setMapHTML] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);

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
    setIsLoading(true);

    try {
      const body = {
        chat_messages: [...messageHistory, question_message],
        session_id: sessionId,
      };
      console.log(body);

      const response = await fetch(`${import.meta.env.VITE_BACKEND_URL}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      if (!response.body) {
        throw new Error("Response body is null");
      }

      // Set up stream reader
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let traceId = "";
      let fullResponse = "";
      let assistantMessageAdded = false;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const jsonLines = chunk.split("\n").filter((line) => line.trim());

        for (const line of jsonLines) {
          try {
            let data = JSON.parse(line);

            traceId = data.trace_id || traceId;

            if (data.response !== undefined) {
              // Add the assistant message only when the first response chunk arrives
              if (!assistantMessageAdded) {
                const assistantMessage: Message = {
                  content: data.response,
                  role: "assistant",
                  trace_id: traceId,
                  is_finished: false,
                };
                setMessageHistory((prev) => [...prev, assistantMessage]);
                assistantMessageAdded = true;
                fullResponse = data.response;
              } else {
                // Update message history with new content
                fullResponse += data.response;
                setMessageHistory((prev) => {
                  const newHistory = [...prev];
                  if (newHistory.length > 0) {
                    newHistory[newHistory.length - 1] = {
                      ...newHistory[newHistory.length - 1],
                      content: fullResponse,
                      trace_id: traceId,
                    };
                  }
                  return newHistory;
                });
              }
            }

            // Mark message as finished when server sends is_finish flag
            if (data.is_finished && assistantMessageAdded) {
              setMessageHistory((prev) => {
                const newHistory = [...prev];
                if (newHistory.length > 0) {
                  newHistory[newHistory.length - 1] = {
                    ...newHistory[newHistory.length - 1],
                    is_finished: true,
                  };
                }
                return newHistory;
              });
            }

            if (data.is_html && data.html_content) {
              setMapHTML(data.html_content);
            }

            if (data.tool_call && data.tool_call !== "") {
              setToolCalls((prev) => {
                const existingQuestionIndex = prev.findIndex(
                  (item) => item.question === question
                );

                const toolCallsArray = Array.isArray(data.tool_call)
                  ? data.tool_call
                  : [data.tool_call];

                if (existingQuestionIndex >= 0) {
                  // Question exists, add each tool call as a step to its toolCalls array
                  const updatedToolCalls = [...prev];
                  updatedToolCalls[existingQuestionIndex] = {
                    ...updatedToolCalls[existingQuestionIndex],
                    toolCalls: [
                      ...updatedToolCalls[existingQuestionIndex].toolCalls,
                      ...toolCallsArray,
                    ],
                  };
                  return updatedToolCalls;
                } else {
                  // Question doesn't exist yet, create a new entry
                  return [
                    ...prev,
                    { question: question, toolCalls: toolCallsArray },
                  ];
                }
              });
            }
          } catch (e) {
            console.error("Error parsing streaming response:", e, line);
          }
        }
      }
    } catch (error) {
      console.error(error);
      const error_message = {
        content: "Sorry, there was an error processing your request.",
        role: "assistant" as const,
        trace_id: generateUUID(),
      };
      setMessageHistory((prev) => [...prev, error_message]);
    } finally {
      setIsLoading(false);
    }
  }

  function switchTab(tab: "chat" | "tools"): void {
    setActiveTab(tab);
  }

  return (
    <div className="app-container">
      <div className="container">
        <MapContainer mapHTML={mapHTML} />
        <ChatSection
          activeTab={activeTab}
          messageHistory={messageHistory}
          toolCalls={toolCalls}
          switchTab={switchTab}
          askQuestion={askQuestion}
          isLoading={isLoading}
        />
      </div>
      <UserGuide />
    </div>
  );
}

export default App;
