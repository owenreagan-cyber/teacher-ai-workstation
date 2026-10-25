// @ts-check
const { defineConfig } = require('@playwright/test');
const path = require('path');

const PORT = 4311;
const FIXTURE_STATE = path.join(__dirname, '.fixture-state');

module.exports = defineConfig({
  testDir: __dirname,
  testMatch: '*.spec.js',
  timeout: 30_000,
  fullyParallel: false,
  workers: 1,
  reporter: [['list']],
  use: {
    baseURL: `http://127.0.0.1:${PORT}`,
    headless: true,
    screenshot: 'only-on-failure',
    trace: 'off',
  },
  globalSetup: require.resolve('./global-setup.js'),
  webServer: {
    command: `TAW_STATE_ROOT=${FIXTURE_STATE} python3 ${path.join(__dirname, 'start_server.py')} ${PORT}`,
    url: `http://127.0.0.1:${PORT}/api/status`,
    reuseExistingServer: false,
    timeout: 20_000,
  },
});
