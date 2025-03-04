interface Message {
  trace_id: string;
  content: string;
  role: "user" | "assistant";
  feedback_given?: number;
  is_finished?: boolean;
}

export type { Message };
