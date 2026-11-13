const fs = require("node:fs");
const path = require("node:path");

const source = path.resolve(__dirname, "../node_modules/@mediapipe/holistic");
const target = path.resolve(__dirname, "../public/mediapipe");
if (!fs.existsSync(source))
  throw new Error("MediaPipe Holistic package was not installed.");
fs.rmSync(target, { recursive: true, force: true });
fs.mkdirSync(target, { recursive: true });
for (const entry of fs.readdirSync(source, { withFileTypes: true })) {
  if (entry.isFile())
    fs.copyFileSync(
      path.join(source, entry.name),
      path.join(target, entry.name),
    );
}
console.log(
  "Copied local MediaPipe runtime assets to frontend/public/mediapipe",
);
