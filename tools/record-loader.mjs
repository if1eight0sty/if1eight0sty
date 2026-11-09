#!/usr/bin/env node
/**
 * Capture the portfolio boot loader as a frame sequence.
 *
 * Usage: node tools/record-loader.mjs <url> <frames-dir> [durationMs]
 *
 * Requires a Chrome/Chromium binary (CHROME_BIN, or auto-detected) and a
 * running portfolio dev server. Frames land in <frames-dir>/frame_0000.png….
 * Encode them with tools/record-loader.sh, not directly.
 */

import { spawn } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import { setTimeout as sleep } from "node:timers/promises";

const url = process.argv[2] ?? "http://localhost:5173/?boot=1";
const outDir = process.argv[3] ?? "frames";
const durationMs = Number(process.argv[4] ?? 5200);
const port = Number(process.env.CDP_PORT ?? 9351);

if (typeof WebSocket === "undefined") {
  console.error("ERROR: Node 22+ required (global WebSocket).");
  process.exit(1);
}

const candidates = [
  process.env.CHROME_BIN,
  "google-chrome-stable",
  "google-chrome",
  "chromium",
  "chromium-browser",
].filter(Boolean);

function findChrome() {
  for (const bin of candidates) {
    const probe = spawn(bin, ["--version"], { stdio: "ignore" });
    if (probe.pid) return bin;
  }
  console.error("ERROR: no Chrome/Chromium found. Set CHROME_BIN.");
  process.exit(1);
}

const chromeBin = findChrome();
mkdirSync(outDir, { recursive: true });

const chrome = spawn(
  chromeBin,
  [
    "--headless=new",
    "--disable-gpu",
    "--hide-scrollbars",
    "--no-sandbox",
    `--remote-debugging-port=${port}`,
    "--window-size=1100,520",
    "about:blank",
  ],
  { stdio: "ignore" },
);

let ws;
try {
  let wsUrl;
  for (let i = 0; i < 80 && !wsUrl; i++) {
    try {
      const list = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
      wsUrl = list.find((t) => t.type === "page")?.webSocketDebuggerUrl;
    } catch {
      /* chrome not up yet */
    }
    if (!wsUrl) await sleep(250);
  }
  if (!wsUrl) throw new Error("Chrome debugging endpoint never came up");

  ws = new WebSocket(wsUrl);
  await new Promise((resolve, reject) => {
    ws.onopen = resolve;
    ws.onerror = reject;
  });

  let id = 0;
  const pending = new Map();
  let frameNo = 0;
  let recording = false;

  ws.onmessage = async (event) => {
    const msg = JSON.parse(event.data);
    if (msg.method === "Page.screencastFrame" && recording) {
      const { data, sessionId } = msg.params;
      writeFileSync(`${outDir}/frame_${String(frameNo).padStart(4, "0")}.png`, Buffer.from(data, "base64"));
      frameNo++;
      try {
        await send("Page.screencastFrameAck", { sessionId });
      } catch {
        /* stream closed */
      }
      return;
    }
    if (msg.id && pending.has(msg.id)) {
      const { resolve, reject } = pending.get(msg.id);
      pending.delete(msg.id);
      msg.error ? reject(new Error(JSON.stringify(msg.error))) : resolve(msg.result);
    }
  };

  const send = (method, params = {}) =>
    new Promise((resolve, reject) => {
      const msgId = ++id;
      pending.set(msgId, { resolve, reject });
      ws.send(JSON.stringify({ id: msgId, method, params }));
    });

  const evaluate = async (expression) =>
    (await send("Runtime.evaluate", { expression, returnByValue: true })).result?.value;

  await send("Page.enable");
  await send("Runtime.enable");
  await send("Emulation.setDeviceMetricsOverride", {
    width: 1100,
    height: 520,
    deviceScaleFactor: 1,
    mobile: false,
  });
  await send("Page.navigate", { url });

  // Wait for hydration: the loader mounts after the app boots.
  for (let i = 0; i < 300; i++) {
    const ready = await evaluate('!!document.querySelector(\'[aria-label="Loading portfolio"] canvas\')');
    if (ready) break;
    await sleep(100);
  }

  recording = true;
  await send("Page.startScreencast", { format: "png", maxWidth: 1100, maxHeight: 520, everyNthFrame: 1 });
  await sleep(durationMs);
  await send("Page.stopScreencast");
  recording = false;

  console.log(`captured ${frameNo} frames into ${outDir}`);
} finally {
  try {
    ws?.close();
  } catch {
    /* ignore */
  }
  chrome.kill("SIGKILL");
}
