const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");
const { pathToFileURL } = require("url");

const OUT_DIR = __dirname;
const HTML = path.join(OUT_DIR, "paper_workflow_posters.html");
const CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const W = 1080;
const H = 1920;

const posters = [
  "poster-01-workflow-engine.png",
  "poster-02-hard-gates.png",
  "poster-03-evidence-ledger.png",
  "poster-04-backend-router.png",
  "poster-05-submission-pack.png",
];

if (!fs.existsSync(CHROME)) {
  throw new Error(`Chrome not found at ${CHROME}`);
}

for (let i = 0; i < posters.length; i += 1) {
  const out = path.join(OUT_DIR, posters[i]);
  const url = `${pathToFileURL(HTML).href}?poster=${i + 1}`;
  const result = spawnSync(CHROME, [
    "--headless=new",
    "--disable-gpu",
    "--hide-scrollbars",
    "--allow-file-access-from-files",
    "--force-device-scale-factor=1",
    `--window-size=${W},${H}`,
    `--screenshot=${out}`,
    url,
  ], { stdio: "inherit" });

  if (result.status !== 0) {
    throw new Error(`Failed to render ${posters[i]}`);
  }
}
