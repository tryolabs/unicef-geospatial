function TabNav({
  activeTab,
  switchTab,
}: {
  activeTab: "chat" | "tools";
  switchTab: (tab: "chat" | "tools") => void;
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
        className={`tab ${activeTab === "tools" ? "active" : ""}`}
        onClick={() => switchTab("tools")}
      >
        Tool Calls
      </div>
    </div>
  );
}

export default TabNav;
