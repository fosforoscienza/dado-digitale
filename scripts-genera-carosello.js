#!/usr/bin/env node

/**
 * Genera automaticamente un carosello Instagram (formato 1080x1350) a partire da un testo.
 * Output: una cartella con file HTML già impaginati, uno per slide.
 *
 * Uso:
 *   node scripts-genera-carosello.js --input testo.txt --output dist/carousel
 */

const fs = require('fs');
const path = require('path');

const WIDTH = 1080;
const HEIGHT = 1350;
const MAX_CHARS_PER_SLIDE = 220;
const DEFAULT_TITLE = 'Carosello automatico';

function parseArgs(argv) {
  const args = {};
  for (let i = 2; i < argv.length; i++) {
    const current = argv[i];
    if (current.startsWith('--')) {
      const key = current.slice(2);
      const value = argv[i + 1] && !argv[i + 1].startsWith('--') ? argv[++i] : true;
      args[key] = value;
    }
  }
  return args;
}

function ensureDir(targetDir) {
  fs.mkdirSync(targetDir, { recursive: true });
}

function chunkText(text, maxChars) {
  const paragraphs = text
    .split(/\n\s*\n/g)
    .map((p) => p.trim())
    .filter(Boolean);

  const chunks = [];
  let buffer = '';

  for (const paragraph of paragraphs) {
    const candidate = buffer ? `${buffer}\n\n${paragraph}` : paragraph;
    if (candidate.length <= maxChars) {
      buffer = candidate;
      continue;
    }

    if (buffer) {
      chunks.push(buffer);
      buffer = '';
    }

    if (paragraph.length <= maxChars) {
      buffer = paragraph;
      continue;
    }

    const sentences = paragraph.split(/(?<=[.!?])\s+/g);
    let sentenceBuffer = '';
    for (const sentence of sentences) {
      const sentenceCandidate = sentenceBuffer ? `${sentenceBuffer} ${sentence}` : sentence;
      if (sentenceCandidate.length <= maxChars) {
        sentenceBuffer = sentenceCandidate;
      } else {
        if (sentenceBuffer) chunks.push(sentenceBuffer);
        sentenceBuffer = sentence;
      }
    }
    if (sentenceBuffer) {
      buffer = sentenceBuffer;
    }
  }

  if (buffer) chunks.push(buffer);
  return chunks;
}

function escapeHtml(value) {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

function htmlTemplate({ title, body, slideNumber, totalSlides }) {
  return `<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=${WIDTH}, initial-scale=1" />
  <title>${title} · ${slideNumber}/${totalSlides}</title>
  <style>
    :root {
      --bg: #0b0f1a;
      --accent: #7c5cff;
      --text: #ffffff;
      --muted: #bac3d6;
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
      background: var(--bg);
      color: var(--text);
      width: ${WIDTH}px;
      height: ${HEIGHT}px;
    }

    .frame {
      width: 100%;
      height: 100%;
      padding: 90px 86px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      background:
        radial-gradient(circle at 12% 10%, rgba(124, 92, 255, 0.24) 0%, rgba(124, 92, 255, 0) 43%),
        radial-gradient(circle at 94% 98%, rgba(0, 221, 255, 0.20) 0%, rgba(0, 221, 255, 0) 35%),
        linear-gradient(160deg, #121936 0%, #0a0f1f 75%);
    }

    .title {
      font-size: 64px;
      line-height: 1.05;
      font-weight: 800;
      max-width: 92%;
      margin: 0;
    }

    .body {
      white-space: pre-line;
      font-size: 46px;
      line-height: 1.28;
      color: #f5f7ff;
      margin: 50px 0 32px;
      letter-spacing: 0.1px;
    }

    .footer {
      display: flex;
      justify-content: space-between;
      align-items: center;
      color: var(--muted);
      font-size: 28px;
      font-weight: 600;
    }

    .pill {
      padding: 10px 22px;
      border-radius: 999px;
      border: 1px solid rgba(255,255,255,0.26);
      background: rgba(255,255,255,0.08);
    }
  </style>
</head>
<body>
  <section class="frame">
    <header>
      <h1 class="title">${escapeHtml(title)}</h1>
      <div class="body">${escapeHtml(body)}</div>
    </header>

    <footer class="footer">
      <span class="pill">@tuoprofilo</span>
      <span>${slideNumber}/${totalSlides}</span>
    </footer>
  </section>
</body>
</html>`;
}

function buildIndex(slides, title) {
  const links = slides
    .map((filename, idx) => `<li><a href="./${filename}">Slide ${idx + 1}</a></li>`)
    .join('\n');

  return `<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8" />
  <title>${title}</title>
</head>
<body>
  <h1>${title}</h1>
  <ol>${links}</ol>
  <p>Per esportare in PNG puoi aprire ogni slide nel browser e fare screenshot in dimensione originale (1080x1350).</p>
</body>
</html>`;
}

function main() {
  const args = parseArgs(process.argv);
  const inputPath = args.input;
  const outputDir = args.output || 'dist/carousel';
  const title = args.title || DEFAULT_TITLE;

  if (!inputPath) {
    console.error('Errore: usa --input <file.txt>.');
    process.exit(1);
  }

  if (!fs.existsSync(inputPath)) {
    console.error(`Errore: file input non trovato: ${inputPath}`);
    process.exit(1);
  }

  const text = fs.readFileSync(inputPath, 'utf8').trim();
  if (!text) {
    console.error('Errore: file di input vuoto.');
    process.exit(1);
  }

  const slidesText = chunkText(text, Number(args.maxChars || MAX_CHARS_PER_SLIDE));
  ensureDir(outputDir);

  const slideFiles = [];

  slidesText.forEach((slideBody, idx) => {
    const slideNumber = idx + 1;
    const totalSlides = slidesText.length;
    const filename = `slide-${String(slideNumber).padStart(2, '0')}.html`;
    const html = htmlTemplate({
      title,
      body: slideBody,
      slideNumber,
      totalSlides,
    });

    fs.writeFileSync(path.join(outputDir, filename), html, 'utf8');
    slideFiles.push(filename);
  });

  fs.writeFileSync(path.join(outputDir, 'index.html'), buildIndex(slideFiles, title), 'utf8');

  console.log(`Creati ${slideFiles.length} slide in: ${outputDir}`);
  console.log('Prossimo step: apri index.html e salva ogni slide come immagine 1080x1350.');
}

main();
