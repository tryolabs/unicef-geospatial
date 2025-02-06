function ChainOfThoughtSection({
  chainOfThoughts,
}: {
  chainOfThoughts: Array<{
    question: string;
    thoughts: Array<string | object>;
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
      {chainOfThoughts.map((item, idx) => (
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
            {item.thoughts.map((thought, tIndex) => (
              <div className="thought-step" key={tIndex}>
                {tIndex === 0 ? (
                  <strong>Initial Thought</strong>
                ) : (
                  <strong>Step {tIndex}</strong>
                )}
                <pre>
                  {typeof thought === "object"
                    ? JSON.stringify(thought, null, 2)
                    : thought}
                </pre>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

export default ChainOfThoughtSection;
