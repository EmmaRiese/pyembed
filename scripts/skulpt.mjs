// Skulpt publishes no releases (npm 1.2.0 is from 2022); skulpt.org serves builds
// of its main branch. We keep a copy in vendor/ and record what we copied in
// vendor/skulpt.json.
//   npm run skulpt         download skulpt.org's current build into vendor/
//   npm run skulpt:check   exit 1 if skulpt.org's build differs from our copy
//                          (run weekly by .github/workflows/skulpt-watch.yml)
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';

const BASE = 'https://skulpt.org/js/';
const FILES = ['skulpt.min.js', 'skulpt-stdlib.js'];
const RECORD = 'vendor/skulpt.json';
const sha256 = buf => createHash('sha256').update(buf).digest('hex');

async function fetchFile(name) {
  const res = await fetch(BASE + name);
  if (!res.ok) throw new Error(`${BASE + name}: HTTP ${res.status}`);
  return { body: Buffer.from(await res.arrayBuffer()),
           lastModified: res.headers.get('last-modified') };
}

if (process.argv.includes('--check')) {
  const record = JSON.parse(readFileSync(RECORD, 'utf8'));
  const changed = [];
  for (const name of FILES) {
    const { body, lastModified } = await fetchFile(name);
    if (sha256(body) !== record.files[name].sha256)
      changed.push(`${name}: ours ${record.files[name].last_modified}, skulpt.org ${lastModified}`);
  }
  if (changed.length) {
    console.log('Skulpt on skulpt.org has changed:\n' + changed.join('\n'));
    process.exit(1);
  }
  console.log('Skulpt unchanged since', record.fetched);
} else {
  const record = { source: BASE, fetched: new Date().toISOString().slice(0, 10), files: {} };
  for (const name of FILES) {
    const { body, lastModified } = await fetchFile(name);
    writeFileSync(`vendor/${name}`, body);
    record.files[name] = { last_modified: lastModified, sha256: sha256(body) };
  }
  writeFileSync(RECORD, JSON.stringify(record, null, 2) + '\n');
  console.log(record);
}
