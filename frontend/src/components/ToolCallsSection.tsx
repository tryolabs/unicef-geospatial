function ToolCallsSection({
  toolCalls,
}: {
  toolCalls: Array<{
    question: string;
    toolCalls: Array<string | object>;
  }>;
}) {
  return (
    <div
      id="chain-of-thought-container"
      style={{
        flex: 1,
        overflowY: "auto",
        backgroundColor: "#fff",
        display: "flex",
        flexDirection: "column",
        gap: "20px",
        padding: "20px",
      }}
    >
      {toolCalls.map((item, idx) => (
        <div key={idx} style={{ marginBottom: "20px" }}>
          <div className="thought-question">
            <strong>Question:</strong> {item.question}
          </div>
          <hr
            style={{
              margin: "15px 0",
              border: "none",
              borderTop: "1px solid var(--border-color)",
            }}
          />
          <div
            style={{ display: "flex", flexDirection: "column", gap: "15px" }}
          >
            {item.toolCalls.map((toolCall, tIndex) => (
              <div className="thought-step" key={tIndex}>
                <strong>Step {tIndex + 1}</strong>
                <pre>
                  {typeof toolCall === "object"
                    ? JSON.stringify(toolCall, null, 2)
                    : toolCall}
                </pre>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

export default ToolCallsSection;
