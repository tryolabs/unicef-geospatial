import { useState, useEffect } from "react";
import MapContainer from "./components/MapContainer.js";
import ChatSection from "./components/ChatSection.js";
import UserGuide from "./components/UserGuide.js";
import Login from "./components/Login.js";
import { Message } from "./types/Message.js";
import { LoginCredentials } from "./types/Auth.js";
import AuthService from "./services/AuthService.js";
import { API_URL } from "./utils/constants.js";
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
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [loginError, setLoginError] = useState<string | null>(null);

  useEffect(() => {
    setSessionId(generateUUID());
    const authEnabled = import.meta.env.VITE_AUTH_ENABLED === "true";
    if (authEnabled) {
      checkAuthentication();
    } else {
      setIsAuthenticated(true);
    }
  }, []);

  async function checkAuthentication() {
    if (AuthService.isAuthenticated()) {
      try {
        const user = await AuthService.getCurrentUser();
        if (user) {
          setIsAuthenticated(true);
        } else {
          setIsAuthenticated(false);
        }
      } catch (error) {
        console.error("Authentication check failed:", error);
        setIsAuthenticated(false);
      }
    }
  }

  async function handleLogin(credentials: LoginCredentials): Promise<void> {
    setLoginError(null);
    try {
      await AuthService.login(credentials);
      setIsAuthenticated(true);
    } catch (error) {
      console.error("Login failed:", error);
      setLoginError("Invalid username or password");
    }
  }

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

      const response = await fetch(`${API_URL}/ask`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...AuthService.getAuthHeaders(),
        },
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
      let fullThinkingResponse = "";
      let finalResponse = "";
      let assistantThinkingMessageAdded = false;
      let assistantFinalMessageAdded = false;
      let buffer = ""; // Buffer to accumulate incomplete chunks

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        buffer += chunk; // Add the new chunk to our buffer

        // Split by newlines but keep any potential incomplete JSON at the end
        const lines = buffer.split("\n");
        // The last line might be incomplete, so we keep it in the buffer
        buffer = lines.pop() || "";

        // Process all complete lines
        for (const line of lines) {
          if (!line.trim()) continue; // Skip empty lines

          try {
            let data = JSON.parse(line);

            traceId = data.trace_id || traceId;

            if (data.response !== undefined) {
              // Handle thinking chunks differently from the final response
              const isThinkingChunk = data.trace_id.startsWith("th_");
              if (isThinkingChunk) {
                // Handle thinking response chunks
                if (!assistantThinkingMessageAdded) {
                  const assistantMessage: Message = {
                    content: data.response,
                    role: "assistant",
                    trace_id: traceId,
                    is_finished: false,
                    is_thinking: true,
                  };
                  setMessageHistory((prev) => [...prev, assistantMessage]);
                  assistantThinkingMessageAdded = true;
                  fullThinkingResponse = data.response;
                } else if (data.response !== "") {
                  // Update thinking message with new content
                  fullThinkingResponse += data.response;
                  setMessageHistory((prev) => {
                    const newHistory = [...prev];
                    const thinkingMessageIndex = newHistory.findIndex(
                      (msg) =>
                        msg.is_thinking &&
                        !msg.is_finished &&
                        msg.trace_id === traceId
                    );
                    if (thinkingMessageIndex >= 0) {
                      newHistory[thinkingMessageIndex] = {
                        ...newHistory[thinkingMessageIndex],
                        content: fullThinkingResponse,
                      };
                    }
                    return newHistory;
                  });
                }

                // Mark thinking message as finished when server signals it's done
                if (data.is_finished && assistantThinkingMessageAdded) {
                  setMessageHistory((prev) => {
                    const newHistory = [...prev];
                    const thinkingMessageIndex = newHistory.findIndex(
                      (msg) =>
                        msg.is_thinking &&
                        !msg.is_finished &&
                        msg.role === "assistant" &&
                        msg.trace_id === traceId
                    );
                    if (thinkingMessageIndex >= 0) {
                      newHistory[thinkingMessageIndex] = {
                        ...newHistory[thinkingMessageIndex],
                        is_finished: true,
                      };
                    }
                    return newHistory;
                  });
                }
              } else {
                // Handle final response (non-thinking chunk)
                if (!assistantFinalMessageAdded && data.response !== "") {
                  const assistantMessage: Message = {
                    content: data.response,
                    role: "assistant",
                    trace_id: traceId,
                    is_finished: false,
                    is_thinking: false,
                  };
                  setMessageHistory((prev) => [...prev, assistantMessage]);
                  assistantFinalMessageAdded = true;
                  finalResponse = data.response;
                } else if (data.response !== "") {
                  // Update final response with new content
                  finalResponse += data.response;
                  setMessageHistory((prev) => {
                    const newHistory = [...prev];
                    const finalMessageIndex = newHistory.findIndex(
                      (msg) =>
                        !msg.is_thinking &&
                        !msg.is_finished &&
                        msg.role === "assistant" &&
                        msg.trace_id === traceId
                    );
                    if (finalMessageIndex >= 0) {
                      newHistory[finalMessageIndex] = {
                        ...newHistory[finalMessageIndex],
                        content: finalResponse,
                      };
                    }
                    return newHistory;
                  });
                }

                // Mark final message as finished
                if (data.is_finished && assistantFinalMessageAdded) {
                  setMessageHistory((prev) => {
                    const newHistory = [...prev];
                    const finalMessageIndex = newHistory.findIndex(
                      (msg) =>
                        !msg.is_thinking &&
                        !msg.is_finished &&
                        msg.trace_id === traceId
                    );
                    if (finalMessageIndex >= 0) {
                      newHistory[finalMessageIndex] = {
                        ...newHistory[finalMessageIndex],
                        is_finished: true,
                      };
                    }
                    return newHistory;
                  });
                }
              }
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

  if (!isAuthenticated) {
    return <Login onLogin={handleLogin} loginError={loginError} />;
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
