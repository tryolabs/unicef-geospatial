function MapContainer({ mapHTML }: { mapHTML: string }) {
  // Helper to create an object URL for the iframe
  function createObjectURL(html: string): string {
    const blob = new Blob([html], { type: "text/html" });
    return URL.createObjectURL(blob);
  }

  return (
    <div id="map-container" style={{ flex: 0.6 }}>
      <iframe
        id="map-frame"
        src={mapHTML ? createObjectURL(mapHTML) : "about:blank"}
        style={{
          width: "100%",
          height: "100%",
          border: "none",
          overflow: "hidden",
        }}
      />
    </div>
  );
}

export default MapContainer;
