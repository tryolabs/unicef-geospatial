import TabNav from "./TabNav.js";
import ChatMessages from "./ChatMessages.js";
import ToolCallsSection from "./ToolCallsSection.js";
import InputContainer from "./InputContainer.js";
import { Message } from "../types/Message.js";

function ChatSection({
  activeTab,
  messageHistory,
  toolCalls,
  switchTab,
  askQuestion,
  isLoading,
}: {
  activeTab: "chat" | "tools";
  messageHistory: Message[];
  toolCalls: Array<{
    question: string;
    toolCalls: string[];
  }>;
  switchTab: (tab: "chat" | "tools") => void;
  askQuestion: (question: string) => Promise<void>;
  isLoading: boolean;
}) {
  return (
    <div
      className="chat-section"
      style={{ flex: 0.4, display: "flex", flexDirection: "column" }}
    >
      <TabNav activeTab={activeTab} switchTab={switchTab} />

      {activeTab === "chat" && (
        <ChatMessages
          messageHistory={messageHistory}
          askQuestion={askQuestion}
        />
      )}
      {activeTab === "tools" && <ToolCallsSection toolCalls={toolCalls} />}

      {activeTab === "chat" && (
        <InputContainer askQuestion={askQuestion} isLoading={isLoading} />
      )}
    </div>
  );
}

export default ChatSection;
