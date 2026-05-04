import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Nexudo Mail",
    short_name: "Nexudo",
    description: "Self-hosted email hosting and SMTP API platform",
    start_url: "/login",
    display: "standalone",
    background_color: "#06111f",
    theme_color: "#4de0c1",
    icons: [],
  };
}
