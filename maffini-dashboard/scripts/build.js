'use strict';
// Bundle = concat puro de public/views/*.js → public/bundle.js
// Sem esbuild — replica lesson learned do agentic-os Wave v5.

const fs = require('fs');
const path = require('path');

const viewsDir = path.join(__dirname, '..', 'public', 'views');
const outFile = path.join(__dirname, '..', 'public', 'bundle.js');

const files = fs.readdirSync(viewsDir).filter(f => f.endsWith('.js')).sort();
const bundle = files.map(f => fs.readFileSync(path.join(viewsDir, f), 'utf8')).join('\n');
fs.writeFileSync(outFile, bundle);
console.log(`bundled ${files.length} views → public/bundle.js (${bundle.length} bytes)`);
