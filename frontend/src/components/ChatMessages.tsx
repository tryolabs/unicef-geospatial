import { Message } from "../types/Message.tsx";
import { LangfuseWeb } from "langfuse";
import { useState } from "react";

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
    "What was the frequency of heatwaves in Uruguay in the 1990s?",
    "How many children were born in Ethiopia in 2020?",
    "How many children were globally affected by droughts in 2020?",
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
          const hasGivenFeedback = feedbackState[msg.trace_id] !== undefined;
          const feedbackValue = feedbackState[msg.trace_id];

          return (
            <div
              key={msg.trace_id}
              className={`message-container ${
                isUserMessage
                  ? "user-message-container"
                  : "assistant-message-container"
              }`}
            >
              <div
                className={`message ${
                  isUserMessage ? "user-message" : "assistant-message"
                }`}
              >
                {msg.content}
              </div>
              {!isUserMessage && msg.is_finished && (
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
