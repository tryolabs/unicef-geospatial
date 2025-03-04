import { Message } from "../types/Message.tsx";

export interface ChatSectionProps {
  activeTab: "chat" | "tools";
  messageHistory: Message[];
  toolCalls: Array<{ question: string; toolCalls: string[] }>;
  switchTab: (tab: "chat" | "tools") => void;
  askQuestion: (question: string) => Promise<void>;
  isLoading: boolean;
}
