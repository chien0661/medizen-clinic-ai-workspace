#!/usr/bin/env node
/**
 * Export markdown to PDF with PlantUML diagrams rendered as images.
 * Usage: node scripts/export-pdf.js <input.md> <output.pdf>
 */

const fs = require('fs');
const path = require('path');
const zlib = require('zlib');
const https = require('https');
const http = require('http');
const { execSync } = require('child_process');

// --- PlantUML encoding ---
const PLANTUML_ALPHABET = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_';

function encode6bit(b) {
  return PLANTUML_ALPHABET[b & 0x3F];
}

function append3bytes(b1, b2, b3) {
  const c1 = b1 >> 2;
  const c2 = ((b1 & 0x3) << 4) | (b2 >> 4);
  const c3 = ((b2 & 0xF) << 2) | (b3 >> 6);
  const c4 = b3 & 0x3F;
  return encode6bit(c1) + encode6bit(c2) + encode6bit(c3) + encode6bit(c4);
}

function encodePlantUML(data) {
  const compressed = zlib.deflateRawSync(Buffer.from(data, 'utf8'), { level: 9 });
  let result = '';
  for (let i = 0; i < compressed.length; i += 3) {
    if (i + 2 < compressed.length) {
      result += append3bytes(compressed[i], compressed[i + 1], compressed[i + 2]);
    } else if (i + 1 < compressed.length) {
      result += append3bytes(compressed[i], compressed[i + 1], 0);
    } else {
      result += append3bytes(compressed[i], 0, 0);
    }
  }
  return result;
}

function getPlantUMLImageUrl(code) {
  const encoded = encodePlantUML(code);
  return `https://www.plantuml.com/plantuml/png/${encoded}`;
}

function downloadImage(url) {
  return new Promise((resolve, reject) => {
    const client = url.startsWith('https') ? https : http;
    client.get(url, (res) => {
      if (res.statusCode === 301 || res.statusCode === 302) {
        downloadImage(res.headers.location).then(resolve).catch(reject);
        return;
      }
      const chunks = [];
      res.on('data', chunk => chunks.push(chunk));
      res.on('end', () => resolve(Buffer.concat(chunks)));
      res.on('error', reject);
    }).on('error', reject);
  });
}

// --- Markdown to HTML (minimal) ---
function escapeHtml(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

async function markdownToHtml(mdContent) {
  // Normalize CRLF to LF (Windows line endings fix)
  mdContent = mdContent.replace(/\r\n/g, '\n').replace(/\r/g, '\n');

  // Extract and render PlantUML blocks first
  const plantUMLBlocks = [];
  let processed = mdContent;

  const pumlRegex = /```plantuml\n([\s\S]*?)```/g;
  let match;
  let i = 0;
  while ((match = pumlRegex.exec(mdContent)) !== null) {
    const code = match[1];
    const url = getPlantUMLImageUrl(code);
    console.log(`  Rendering PlantUML diagram ${i + 1} from: ${url}`);
    try {
      const imgBuffer = await downloadImage(url);
      const base64 = imgBuffer.toString('base64');
      plantUMLBlocks.push(`<div class="diagram"><img src="data:image/png;base64,${base64}" alt="Sequence Diagram" style="max-width:100%;"/></div>`);
    } catch (e) {
      console.warn(`  Warning: could not download diagram, using URL instead. ${e.message}`);
      plantUMLBlocks.push(`<div class="diagram"><img src="${url}" alt="Sequence Diagram" style="max-width:100%;"/></div>`);
    }
    i++;
  }

  // Replace plantuml blocks with placeholders
  let idx = 0;
  processed = processed.replace(/```plantuml\n[\s\S]*?```/g, () => `__PLANTUML_${idx++}__`);

  // Simple markdown conversion
  const lines = processed.split('\n');
  const htmlLines = [];
  let inCodeBlock = false;
  let inTable = false;
  let inList = false;

  for (let li = 0; li < lines.length; li++) {
    let line = lines[li];

    // Code blocks (non-plantuml)
    if (line.startsWith('```')) {
      if (!inCodeBlock) {
        inCodeBlock = true;
        if (inList) { htmlLines.push('</ul>'); inList = false; }
        if (inTable) { htmlLines.push('</tbody></table>'); inTable = false; }
        htmlLines.push('<pre><code>');
      } else {
        inCodeBlock = false;
        htmlLines.push('</code></pre>');
      }
      continue;
    }
    if (inCodeBlock) {
      htmlLines.push(escapeHtml(line));
      continue;
    }

    // PlantUML placeholder
    const pumlMatch = line.match(/__PLANTUML_(\d+)__/);
    if (pumlMatch) {
      if (inTable) { htmlLines.push('</tbody></table>'); inTable = false; }
      if (inList) { htmlLines.push('</ul>'); inList = false; }
      htmlLines.push(plantUMLBlocks[parseInt(pumlMatch[1])]);
      continue;
    }

    // Horizontal rule
    if (/^---+$/.test(line.trim())) {
      if (inTable) { htmlLines.push('</tbody></table>'); inTable = false; }
      if (inList) { htmlLines.push('</ul>'); inList = false; }
      htmlLines.push('<hr/>');
      continue;
    }

    // Table rows
    if (line.startsWith('|')) {
      if (inList) { htmlLines.push('</ul>'); inList = false; }
      if (!inTable) {
        htmlLines.push('<table><thead>');
        inTable = true;
        // header row
        const cells = line.split('|').slice(1, -1).map(c => `<th>${renderInline(c.trim())}</th>`).join('');
        htmlLines.push(`<tr>${cells}</tr>`);
        htmlLines.push('</thead><tbody>');
        // skip separator
        li++;
        continue;
      } else {
        const cells = line.split('|').slice(1, -1).map(c => `<td>${renderInline(c.trim())}</td>`).join('');
        htmlLines.push(`<tr>${cells}</tr>`);
        continue;
      }
    } else if (inTable) {
      htmlLines.push('</tbody></table>');
      inTable = false;
    }

    // Headings
    const h = line.match(/^(#{1,6})\s+(.*)/);
    if (h) {
      if (inList) { htmlLines.push('</ul>'); inList = false; }
      const level = h[1].length;
      htmlLines.push(`<h${level}>${renderInline(h[2])}</h${level}>`);
      continue;
    }

    // List items
    const listMatch = line.match(/^(\s*[-*])\s+(.*)/);
    if (listMatch) {
      if (!inList) { htmlLines.push('<ul>'); inList = true; }
      htmlLines.push(`<li>${renderInline(listMatch[2])}</li>`);
      continue;
    } else if (inList && line.trim() === '') {
      htmlLines.push('</ul>');
      inList = false;
    }

    // Blockquote
    if (line.startsWith('> ')) {
      if (inList) { htmlLines.push('</ul>'); inList = false; }
      htmlLines.push(`<blockquote>${renderInline(line.slice(2))}</blockquote>`);
      continue;
    }

    // Empty line
    if (line.trim() === '') {
      if (!inList) htmlLines.push('<br/>');
      continue;
    }

    // Paragraph
    htmlLines.push(`<p>${renderInline(line)}</p>`);
  }

  if (inTable) htmlLines.push('</tbody></table>');
  if (inList) htmlLines.push('</ul>');

  return htmlLines.join('\n');
}

function renderInline(text) {
  return text
    // Bold
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    // Italic
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    // Inline code
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    // Checkmark
    .replace(/✓/g, '✓')
    // Escape remaining HTML
    .replace(/(?<!<[^>]*)&(?![a-z]+;)/g, '&amp;');
}

const HTML_TEMPLATE = (title, body) => `<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8"/>
<title>${title}</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Segoe UI', Arial, sans-serif; font-size: 13px; color: #1a1a1a; padding: 32px 48px; line-height: 1.6; }
  h1 { font-size: 22px; color: #003366; border-bottom: 2px solid #003366; padding-bottom: 8px; margin: 24px 0 16px; }
  h2 { font-size: 17px; color: #003366; border-left: 4px solid #0066cc; padding-left: 10px; margin: 20px 0 12px; }
  h3 { font-size: 14px; color: #004499; margin: 16px 0 8px; }
  h4 { font-size: 13px; color: #333; margin: 12px 0 6px; }
  p { margin: 6px 0; }
  hr { border: none; border-top: 1px solid #ddd; margin: 20px 0; }
  table { border-collapse: collapse; width: 100%; margin: 12px 0; font-size: 12px; }
  th { background: #003366; color: #fff; padding: 7px 10px; text-align: left; }
  td { padding: 6px 10px; border: 1px solid #ccc; vertical-align: top; }
  tr:nth-child(even) td { background: #f5f8ff; }
  code { background: #f0f0f0; padding: 1px 5px; border-radius: 3px; font-family: 'Courier New', monospace; font-size: 12px; }
  pre { background: #f6f8fa; border: 1px solid #e0e0e0; border-radius: 4px; padding: 12px; margin: 10px 0; overflow-x: auto; }
  pre code { background: none; padding: 0; font-size: 11.5px; }
  blockquote { background: #fff8e1; border-left: 4px solid #ffa000; padding: 8px 14px; margin: 10px 0; color: #555; font-style: italic; }
  ul { padding-left: 22px; margin: 8px 0; }
  li { margin: 3px 0; }
  .diagram { text-align: center; margin: 20px 0; padding: 16px; background: #fafafa; border: 1px solid #e0e0e0; border-radius: 6px; }
  .diagram img { max-width: 700px; }
  @media print {
    body { padding: 20px 32px; }
    h1 { page-break-before: avoid; }
    table { page-break-inside: avoid; }
    .diagram { page-break-inside: avoid; }
  }
</style>
</head>
<body>
${body}
</body>
</html>`;

async function main() {
  const inputMd = process.argv[2];
  const outputPdf = process.argv[3];

  if (!inputMd || !outputPdf) {
    console.error('Usage: node export-pdf.js <input.md> <output.pdf>');
    process.exit(1);
  }

  console.log(`Reading: ${inputMd}`);
  const md = fs.readFileSync(inputMd, 'utf8');
  const title = (md.match(/^#\s+(.+)/m) || ['', path.basename(inputMd)])[1];

  console.log('Converting markdown to HTML...');
  const body = await markdownToHtml(md);

  const htmlPath = outputPdf.replace(/\.pdf$/, '.html');
  const html = HTML_TEMPLATE(title, body);
  fs.writeFileSync(htmlPath, html, 'utf8');
  console.log(`HTML saved: ${htmlPath}`);

  console.log('Generating PDF with headless Chrome...');
  const chromePaths = [
    'C:/Program Files/Google/Chrome/Application/chrome.exe',
    'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
  ];
  const chrome = chromePaths.find(p => fs.existsSync(p));
  if (!chrome) {
    console.error('Chrome not found. Please install Google Chrome.');
    process.exit(1);
  }

  // Serve HTML via localhost so Chrome can render base64 images (file:// blocks them)
  const http = require('http');
  const port = 19876;
  const server = http.createServer((req, res) => {
    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
    fs.createReadStream(htmlPath).pipe(res);
  });
  await new Promise(resolve => server.listen(port, resolve));

  const pdfOut = path.resolve(outputPdf);
  try {
    execSync(
      `"${chrome}" --headless=new --disable-gpu --no-sandbox --print-to-pdf="${pdfOut}" --no-pdf-header-footer "http://localhost:${port}"`,
      { stdio: 'inherit' }
    );
  } finally {
    server.close();
  }
  console.log(`PDF saved: ${pdfOut}`);
}

main().catch(err => {
  console.error('Error:', err.message);
  process.exit(1);
});
