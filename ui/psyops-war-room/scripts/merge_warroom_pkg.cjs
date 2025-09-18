#!/usr/bin/env node
/**
 * Safely merge new War Room scripts / devDeps into existing package.json without overwriting existing entries.
 */
import { readFileSync, writeFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, resolve } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const pkgPath = resolve(__dirname, '..', 'package.json');

const pkg = JSON.parse(readFileSync(pkgPath, 'utf8'));
const addScripts = {
  dev: 'vite',
  build: 'vite build',
  preview: 'vite preview',
  typecheck: 'tsc --noEmit',
  lint: "eslint 'src/**/*.{ts,tsx}'",
  format: 'prettier --write .',
  test: 'vitest run',
  'test:watch': 'vitest'
};

pkg.scripts = { ...addScripts, ...(pkg.scripts || {}) }; // prefer existing user overrides

writeFileSync(pkgPath, JSON.stringify(pkg, null, 2) + '\n');
console.log('Merged War Room scripts into package.json');
