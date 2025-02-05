interface Message {
  trace_id: string;
  content: string;
  role: "user" | "assistant";
  feedback_given?: number;
}

export type { Message };
