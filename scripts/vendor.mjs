// Bundles CodeMirror (versions pinned in package-lock.json) into one ES module,
// vendor/codemirror.js, with the versions in vendor/codemirror.json.
// Run after `npm ci`; the result is committed so GitHub Pages needs no build.
import { build } from 'esbuild';
import { readFileSync, writeFileSync } from 'node:fs';

const lock = JSON.parse(readFileSync('package-lock.json', 'utf8'));
const pkg = JSON.parse(readFileSync('package.json', 'utf8'));
const versions = Object.fromEntries(Object.keys(pkg.dependencies).sort()
  .map(name => [name, lock.packages[`node_modules/${name}`].version]));

await build({
  entryPoints: ['scripts/codemirror-entry.js'],
  bundle: true,
  format: 'esm',
  minify: true,
  target: 'es2020',
  legalComments: 'eof',
  outfile: 'vendor/codemirror.js',
});
writeFileSync('vendor/codemirror.json', JSON.stringify(versions, null, 2) + '\n');
console.log('vendor/codemirror.js:', versions);
