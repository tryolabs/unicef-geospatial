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
      style={{ flex: 1, overflowY: "auto", backgroundColor: "#fff" }}
    >
      {chainOfThoughts.map((item, idx) => (
        <div key={idx} style={{ marginBottom: "20px" }}>
          <div className="thought-question">
            <strong>Question:</strong> {item.question}
          </div>
          <hr />
          <div>
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
