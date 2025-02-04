function ChatMessages({ messageHistory }: { messageHistory: string[] }) {
  return (
    <div id="chat-container" style={{ flex: 1, overflowY: "auto" }}>
      {messageHistory.map((msg: string, i: number) => {
        const isUserMessage = i % 2 === 0; // or use more logic if needed
        return (
          <div
            key={i}
            className={`message ${
              isUserMessage ? "user-message" : "assistant-message"
            }`}
          >
            {msg}
          </div>
        );
      })}
    </div>
  );
}

export default ChatMessages;
