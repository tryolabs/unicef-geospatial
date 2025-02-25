import React from "react";

interface MapContainerProps {
  mapHTML: string;
}

const MapContainer = React.memo(({ mapHTML }: MapContainerProps) => {
  const mapInitialized = React.useRef(false);

  React.useEffect(() => {
    if (!mapInitialized.current) {
      const initialMapHTML = `
        <!DOCTYPE html>
        <html>
          <head>
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
            <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
            <style>
              body { margin: 0; }
              #map { height: 100vh; }
            </style>
          </head>
          <body>
            <div id="map"></div>
            <script>
              const map = L.map('map').setView([20, 0], 2);
              L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors'
              }).addTo(map);
            </script>
          </body>
        </html>
      `;

      const iframe = document.createElement("iframe") as HTMLIFrameElement;
      iframe.srcdoc = initialMapHTML;
      iframe.style.width = "100%";
      iframe.style.height = "100%";
      iframe.style.border = "none";

      const container = document.getElementById("map-container");
      if (container) {
        container.innerHTML = "";
        container.appendChild(iframe);
      }

      mapInitialized.current = true;
    }
  }, []);

  React.useEffect(() => {
    if (mapInitialized.current && mapHTML) {
      const iframe = document.querySelector(
        "#map-container iframe"
      ) as HTMLIFrameElement;
      if (iframe) {
        iframe.srcdoc = mapHTML;
      }
    }
  }, [mapHTML]);

  return <div id="map-container" style={{ width: "100%", height: "100%" }} />;
});

export default MapContainer;
