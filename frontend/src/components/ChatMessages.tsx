import { Message } from "../types/Message.tsx";
import { LangfuseWeb } from "langfuse";
import { useState } from "react";
import ReactMarkdown from "react-markdown";

function ChatMessages({
  messageHistory,
  askQuestion,
}: {
  messageHistory: Message[];
  askQuestion: (question: string) => Promise<void>;
}) {
  const [feedbackState, setFeedbackState] = useState<Record<string, number>>(
    {}
  );

  const handleUserFeedback = async (message: Message, value: number) => {
    const langfuseWeb = new LangfuseWeb({
      publicKey: import.meta.env.VITE_LANGFUSE_PUBLIC_KEY,
    });

    await langfuseWeb.score({
      traceId: message.trace_id,
      name: "user_feedback",
      value,
    });

    setFeedbackState((prev) => ({
      ...prev,
      [message.trace_id]: value,
    }));
  };

  const exampleQuestions = [
    "How many children are exposed to wildfires in Uruguay?",
    "How many children were born in Ethiopia in 2020?",
    "How many children are exposed to coastal floods in Colombia?",
  ];

  const handleExampleClick = (question: string) => {
    askQuestion(question);
  };

  return (
    <div id="chat-container" style={{ flex: 1, overflowY: "auto" }}>
      {messageHistory.length === 0 ? (
        <div className="welcome-container">
          <h3>Welcome to UNICEF Geospatial Analysis Assistant</h3>
          <p>
            Start by asking a question about UNICEF data or geospatial analysis.
          </p>
          <div className="example-questions-chat">
            <div className="example-label">Try asking:</div>
            <div className="example-questions-list">
              {exampleQuestions.map((question, index) => (
                <div
                  key={index}
                  className="example-question"
                  onClick={() => handleExampleClick(question)}
                >
                  {question}
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : (
        messageHistory.map((msg: Message) => {
          const isUserMessage = msg.role === "user";
          const isThinkingMessage = msg.is_thinking;
          const hasGivenFeedback = feedbackState[msg.trace_id] !== undefined;
          const feedbackValue = feedbackState[msg.trace_id];

          return (
            <div
              key={msg.trace_id}
              className={`message-container ${
                isUserMessage
                  ? "user-message-container"
                  : isThinkingMessage
                  ? "thinking-message-container"
                  : "assistant-message-container"
              }`}
            >
              {isThinkingMessage && !isUserMessage && (
                <div className="thinking-label">Thinking...</div>
              )}
              <div
                className={`message ${
                  isUserMessage
                    ? "user-message"
                    : isThinkingMessage
                    ? "thinking-message"
                    : "assistant-message"
                }`}
              >
                <ReactMarkdown>{msg.content}</ReactMarkdown>
              </div>
              {!isUserMessage && !isThinkingMessage && msg.is_finished && (
                <div className="feedback-buttons">
                  <button
                    onClick={() => handleUserFeedback(msg, 1)}
                    disabled={hasGivenFeedback}
                    className={`feedback-button ${
                      hasGivenFeedback && feedbackValue === 1
                        ? "feedback-selected"
                        : ""
                    }`}
                    title={
                      hasGivenFeedback ? "Feedback already given" : "Helpful"
                    }
                  >
                    👍
                  </button>
                  <button
                    onClick={() => handleUserFeedback(msg, 0)}
                    disabled={hasGivenFeedback}
                    className={`feedback-button ${
                      hasGivenFeedback && feedbackValue === 0
                        ? "feedback-selected"
                        : ""
                    }`}
                    title={
                      hasGivenFeedback
                        ? "Feedback already given"
                        : "Not helpful"
                    }
                  >
                    👎
                  </button>
                </div>
              )}
            </div>
          );
        })
      )}
    </div>
  );
}

export default ChatMessages;
