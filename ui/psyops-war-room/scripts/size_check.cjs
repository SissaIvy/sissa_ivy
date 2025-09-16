#!/usr/bin/env node
/* Size budget check for War Room bundle (gzip, whole JS/CSS total).
 * Usage: node scripts/size_check.cjs [distDir] [budgetKb]
 */
const fs = require('fs');
const path = require('path');
const zlib = require('zlib');

const dist = process.argv[2] || 'dist';
const budgetKb = Number(process.argv[3] || 180);

function* walk(dir) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, entry.name);
    if (entry.isDirectory()) yield* walk(p);
    else yield p;
  }
}

let totalGz = 0;
const details = [];
for (const file of walk(dist)) {
  if (!/\.(js|css)$/.test(file)) continue;
  const src = fs.readFileSync(file);
  const gz = zlib.gzipSync(src, { level: 9 });
  totalGz += gz.length;
  details.push([file, gz.length]);
}

details.sort((a, b) => b[1] - a[1]);
const fmt = n => (n / 1024).toFixed(1) + ' KB';
console.log('[size] total (gzip):', fmt(totalGz));
console.log('[size] top files:');
for (const [f, n] of details.slice(0, 8)) console.log('  -', path.basename(f), fmt(n));

if (totalGz / 1024 > budgetKb) {
  console.error(`[size] FAIL: total gzip ${fmt(totalGz)} exceeds budget ${budgetKb} KB`);
  process.exit(1);
} else {
  console.log(`[size] OK: within ${budgetKb} KB budget`);
}
