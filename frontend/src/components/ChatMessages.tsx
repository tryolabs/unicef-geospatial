import { Message } from "../types/Message";
import { LangfuseWeb } from "langfuse";
import { useState } from "react";

function ChatMessages({ messageHistory }: { messageHistory: Message[] }) {
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

  return (
    <div id="chat-container" style={{ flex: 1, overflowY: "auto" }}>
      {messageHistory.map((msg: Message) => {
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
            {!isUserMessage && (
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
                    hasGivenFeedback ? "Feedback already given" : "Not helpful"
                  }
                >
                  👎
                </button>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

export default ChatMessages;
