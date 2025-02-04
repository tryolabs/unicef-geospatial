import { useState } from "react";

function InputContainer({
  askQuestion,
}: {
  askQuestion: (question: string) => Promise<void>;
}) {
  const [inputValue, setInputValue] = useState("");

  function handleSend() {
    if (inputValue.trim()) {
      askQuestion(inputValue);
      setInputValue("");
    }
  }

  return (
    <div id="input-container" style={{ display: "flex" }}>
      <input
        type="text"
        id="question-input"
        style={{ flexGrow: 1, padding: "12px", fontSize: "14px" }}
        placeholder="Ask about global indicators, climate data, or request spatial analysis..."
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        onKeyPress={(e) => {
          if (e.key === "Enter" && inputValue.trim()) {
            askQuestion(inputValue);
            setInputValue("");
          }
        }}
      />
      <button onClick={handleSend}>Send</button>
    </div>
  );
}

export default InputContainer;
