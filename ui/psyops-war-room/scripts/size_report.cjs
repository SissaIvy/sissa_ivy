#!/usr/bin/env node
// Emit dist/size-report.json with gzip sizes for JS/CSS bundles.
const fs = require('fs');
const path = require('path');
const zlib = require('zlib');

const dist = process.argv[2] || 'dist';
const out = path.join(dist, 'size-report.json');

function* walk(dir) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, entry.name);
    if (entry.isDirectory()) yield* walk(p);
    else yield p;
  }
}

let totalGz = 0;
const files = [];
for (const file of walk(dist)) {
  if (!/\.(js|css)$/.test(file)) continue;
  const src = fs.readFileSync(file);
  const gz = zlib.gzipSync(src, { level: 9 });
  totalGz += gz.length;
  files.push({ file: path.relative(dist, file), gzip_bytes: gz.length });
}
files.sort((a, b) => b.gzip_bytes - a.gzip_bytes);

const report = {
  generated_at: new Date().toISOString(),
  total_gzip_bytes: totalGz,
  files
};
fs.writeFileSync(out, JSON.stringify(report, null, 2));
console.log('[size] wrote', out, 'total_gzip_kb=', (totalGz/1024).toFixed(1));
