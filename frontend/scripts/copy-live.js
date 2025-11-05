import { existsSync, copyFileSync, mkdirSync } from 'fs';
import { resolve } from 'path';

const root = process.cwd();
const src = resolve(root, 'public', 'live.html');
const outDir = resolve(root, 'dist');
const dest = resolve(outDir, 'live.html');

try {
  if (!existsSync(outDir)) {
    mkdirSync(outDir, { recursive: true });
  }
  if (existsSync(src)) {
    copyFileSync(src, dest);
    console.log(`[copy-live] Copied live.html to dist`);
  } else {
    console.warn(`[copy-live] Source live.html not found at ${src}`);
  }
} catch (err) {
  console.error('[copy-live] Failed to copy live.html:', err);
  process.exitCode = 1;
}