// Seeds a deterministic fixture state before the web server starts.
const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

module.exports = async function globalSetup() {
  const fixture = path.join(__dirname, '.fixture-state');
  fs.rmSync(fixture, { recursive: true, force: true });
  const seed = path.join(__dirname, 'seed_fixture.py');
  const out = execSync(`python3 "${seed}" "${fixture}"`, { encoding: 'utf-8' });
  // eslint-disable-next-line no-console
  console.log('[seed]', out.trim());
};
