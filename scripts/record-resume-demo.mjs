/**
 * Records a demo GIF of the public resume intelligence flow.
 * Mocks the analyze API so no OpenAI key is required.
 *
 * Usage (from repo root):
 *   1. cd frontend && npm run dev
 *   2. node ../scripts/record-resume-demo.mjs
 */
import { chromium } from "playwright";
import pkg from "gifenc";
const { GIFEncoder, quantize, applyPalette } = pkg;
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import pngjs from "pngjs";

const { PNG } = pngjs;

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "..");
const OUT_GIF = path.join(ROOT, "docs", "assets", "resume-analysis-demo.gif");
const SAMPLE_PDF = path.join(ROOT, "docs", "assets", "sample-resume.pdf");
const MOCK_JSON = path.join(ROOT, "docs", "assets", "mock-analyze-response.json");
const BASE_URL = process.env.DEMO_BASE_URL ?? "http://localhost:3000";

const mockPayload = JSON.parse(fs.readFileSync(MOCK_JSON, "utf8"));

async function capturePng(page) {
  return page.screenshot({ type: "png", fullPage: false });
}

function pngBufferToRgba(buffer) {
  const png = PNG.sync.read(buffer);
  return { width: png.width, height: png.height, data: png.data };
}

function writeGif(frames, width, height) {
  const gif = GIFEncoder();
  for (const frame of frames) {
    const palette = quantize(frame.data, 256);
    const index = applyPalette(frame.data, palette);
    gif.writeFrame(index, width, height, { palette, delay: 900, repeat: 0 });
  }
  gif.finish();
  fs.mkdirSync(path.dirname(OUT_GIF), { recursive: true });
  fs.writeFileSync(OUT_GIF, Buffer.from(gif.bytes()));
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 800 },
    deviceScaleFactor: 1,
  });
  const page = await context.newPage();

  await page.route("**/public/analyze-resume**", async (route) => {
    await new Promise((r) => setTimeout(r, 1200));
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(mockPayload),
    });
  });

  const pngFrames = [];

  await page.goto(`${BASE_URL}/tools/resume-intelligence`, { waitUntil: "networkidle" });
  await page.waitForTimeout(800);
  pngFrames.push(await capturePng(page));

  const input = page.locator('input[type="file"]');
  await input.setInputFiles(SAMPLE_PDF);
  await page.waitForTimeout(600);
  pngFrames.push(await capturePng(page));

  await page.getByRole("button", { name: "Analyze with AI" }).click();
  await page.waitForSelector("text=Strengths", { timeout: 15000 });
  await page.waitForTimeout(1000);
  pngFrames.push(await capturePng(page));

  await page.evaluate(() => window.scrollBy(0, 420));
  await page.waitForTimeout(700);
  pngFrames.push(await capturePng(page));

  await browser.close();

  const rgbaFrames = pngFrames.map(pngBufferToRgba);
  const width = rgbaFrames[0].width;
  const height = rgbaFrames[0].height;
  writeGif(rgbaFrames, width, height);
  console.log(`Wrote ${OUT_GIF} (${pngFrames.length} frames)`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
