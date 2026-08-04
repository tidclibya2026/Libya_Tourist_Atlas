import fs from 'node:fs';

const file = new URL('./test_recovered_media_playwright.py', import.meta.url);
const before = fs.readFileSync(file, 'utf8');
const oldText = ".includes('/assets/images/')";
const newText = ".includes('data-image=\"http://localhost:8080/assets/images/')";

if (!before.includes(oldText)) {
  throw new Error('Expected Playwright marker selector was not found');
}

fs.writeFileSync(file, before.replaceAll(oldText, newText), 'utf8');
