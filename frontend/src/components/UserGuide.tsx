function UserGuide() {
  return (
    <div className="user-guide">
      <h2>UNICEF Geospatial Analysis Assistant</h2>
      <p>
        This tool helps you explore and analyze global data through natural
        language queries. By combining UNICEF's data warehouse indicators with
        geospatial analysis capabilities, it provides insights into important
        development and humanitarian issues affecting children worldwide.
      </p>

      <div className="guide-section">
        <h3>What can you do?</h3>
        <ul>
          <li>
            <strong>Explore UNICEF indicators</strong> - Access data on
            education, health, nutrition, child protection, and other key
            metrics from UNICEF's Data Warehouse
          </li>
          <li>
            <strong>Analyze geospatial patterns</strong> - Visualize data on
            maps to understand geographic distributions and trends
          </li>
          <li>
            <strong>Examine climate data</strong> - View climate-related
            information such as droughts, heatwaves, and environmental factors
            that impact children
          </li>
        </ul>
      </div>

      <div className="guide-section">
        <h3>Available Data</h3>
        <div className="data-types">
          <div className="data-type">
            <h4>🌍 Geospatial Data</h4>
            <ul>
              <li>Droughts data</li>
              <li>Heatwaves data</li>
              <li>Demographic data</li>
            </ul>
          </div>
          <div className="data-type">
            <h4>📊 UNICEF Indicators</h4>
            <ul>
              <li>Child mortality</li>
              <li>Education access</li>
              <li>Nutrition status</li>
              <li>Water and sanitation</li>
              <li>Health coverage</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

export default UserGuide;
