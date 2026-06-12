'use strict';
// Dev mode — restart server on source changes, rebuild on views/* change.
// Zero deps. Uses fs.watch.

const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
let child = null;
let buildTimer = null;
let restartTimer = null;

function rebuild() {
  if (buildTimer) clearTimeout(buildTimer);
  buildTimer = setTimeout(() => {
    const r = spawn('node', [path.join(__dirname, 'build.js')], { stdio: 'inherit' });
    r.on('close', code => {
      if (code === 0) restart();
    });
  }, 200);
}

function restart() {
  if (restartTimer) clearTimeout(restartTimer);
  restartTimer = setTimeout(() => {
    if (child) {
      child.kill('SIGTERM');
      child = null;
    }
    child = spawn('node', [path.join(ROOT, 'server', 'index.js')], { stdio: 'inherit' });
  }, 200);
}

function watchTree(dir, handler) {
  fs.watch(dir, { recursive: true }, (event, filename) => {
    if (!filename) return;
    if (filename.endsWith('.tmp') || filename.startsWith('.')) return;
    handler(event, filename);
  });
}

// Initial build + start
const init = spawn('node', [path.join(__dirname, 'build.js')], { stdio: 'inherit' });
init.on('close', () => {
  child = spawn('node', [path.join(ROOT, 'server', 'index.js')], { stdio: 'inherit' });
  watchTree(path.join(ROOT, 'server'), (_, f) => { console.log(`server change: ${f}`); restart(); });
  watchTree(path.join(ROOT, 'public', 'views'), (_, f) => { console.log(`view change: ${f}`); rebuild(); });
  console.log('dev mode: watching server/ and public/views/');
});

process.on('SIGINT', () => { if (child) child.kill(); process.exit(0); });
process.on('SIGTERM', () => { if (child) child.kill(); process.exit(0); });
