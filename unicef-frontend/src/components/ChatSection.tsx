import TabNav from "./TabNav.js";
import ChatMessages from "./ChatMessages.js";
import ChainOfThoughtSection from "./ChainOfThoughtSection.js";
import InputContainer from "./InputContainer.js";

function ChatSection({
  activeTab,
  messageHistory,
  chainOfThoughts,
  switchTab,
  askQuestion,
}: {
  activeTab: "chat" | "thoughts";
  messageHistory: string[];
  chainOfThoughts: Array<{
    question: string;
    thoughts: string[];
  }>;
  switchTab: (tab: "chat" | "thoughts") => void;
  askQuestion: (question: string) => Promise<void>;
}) {
  return (
    <div
      className="chat-section"
      style={{ flex: 0.4, display: "flex", flexDirection: "column" }}
    >
      <TabNav activeTab={activeTab} switchTab={switchTab} />

      {activeTab === "chat" && <ChatMessages messageHistory={messageHistory} />}
      {activeTab === "thoughts" && (
        <ChainOfThoughtSection chainOfThoughts={chainOfThoughts} />
      )}

      {activeTab === "chat" && <InputContainer askQuestion={askQuestion} />}
    </div>
  );
}

export default ChatSection;
