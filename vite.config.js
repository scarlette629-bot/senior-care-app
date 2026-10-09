import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Each deployed build receives a unique identity. This avoids the PWA falsely
// reporting "already up to date" when features changed but the human version
// number stayed the same. GitHub Pages uses GITHUB_SHA; local builds work too.
const APP_VERSION = "1.0.5";
const BUILD_ID = `${(process.env.GITHUB_SHA || "local").slice(0,12)}-${Date.now().toString(36)}`;
const releaseStamp = {
  name: "wecare-release-identity",
  transformIndexHtml(html) {
    return html.replace(
      /(<meta\s+name="wecare-version"\s+content=")[^"]+(")/,
      (_, prefix, suffix) => prefix + APP_VERSION + "-" + BUILD_ID + suffix
    );
  },
  generateBundle() {
    this.emitFile({
      type: "asset",
      fileName: "version.json",
      source: JSON.stringify({
        version: APP_VERSION,
        build: BUILD_ID,
        publishedAt: new Date().toISOString()
      })
    });
  }
};
export default defineConfig({
  plugins: [react(), releaseStamp],
  define: { __WECARE_BUILD_ID__: JSON.stringify(BUILD_ID) },
  base: "/senior-care-app/"
});
