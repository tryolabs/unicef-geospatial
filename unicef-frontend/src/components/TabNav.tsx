function TabNav({
  activeTab,
  switchTab,
}: {
  activeTab: "chat" | "thoughts";
  switchTab: (tab: "chat" | "thoughts") => void;
}) {
  return (
    <div className="tab-container">
      <div
        className={`tab ${activeTab === "chat" ? "active" : ""}`}
        onClick={() => switchTab("chat")}
      >
        Chat
      </div>
      <div
        className={`tab ${activeTab === "thoughts" ? "active" : ""}`}
        onClick={() => switchTab("thoughts")}
      >
        Chain of Thought
      </div>
    </div>
  );
}

export default TabNav;
