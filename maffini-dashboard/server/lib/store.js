'use strict';
// JSON file store — atomic write (write-rename), schema-light.
// Não substitui DB — pra coleções pequenas (clientes, prazos, settings).

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

function ensureDir(p) { fs.mkdirSync(path.dirname(p), { recursive: true }); }

function readJSON(file, fallback) {
  try {
    const txt = fs.readFileSync(file, 'utf8');
    return JSON.parse(txt);
  } catch { return fallback; }
}

function writeJSON(file, data) {
  ensureDir(file);
  const tmp = `${file}.${process.pid}.tmp`;
  fs.writeFileSync(tmp, JSON.stringify(data, null, 2), { mode: 0o600 });
  fs.renameSync(tmp, file);
}

class JSONStore {
  /**
   * @param {string} file  absolute path to JSON file
   * @param {object} opts  { defaultShape?: any }
   */
  constructor(file, opts = {}) {
    this.file = file;
    this.defaultShape = opts.defaultShape || { items: [] };
  }

  load() { return readJSON(this.file, this.defaultShape); }
  save(data) { writeJSON(this.file, data); }

  list() {
    const d = this.load();
    return Array.isArray(d) ? d : (d.items || []);
  }

  get(id) {
    return this.list().find(x => x.id === id) || null;
  }

  create(record) {
    const d = this.load();
    const items = Array.isArray(d) ? d : (d.items || []);
    const item = Object.assign(
      { id: crypto.randomUUID(), createdAt: new Date().toISOString() },
      record
    );
    items.push(item);
    if (Array.isArray(d)) this.save(items);
    else this.save(Object.assign({}, d, { items }));
    return item;
  }

  update(id, patch) {
    const d = this.load();
    const items = Array.isArray(d) ? d : (d.items || []);
    const idx = items.findIndex(x => x.id === id);
    if (idx < 0) return null;
    items[idx] = Object.assign({}, items[idx], patch, {
      updatedAt: new Date().toISOString()
    });
    if (Array.isArray(d)) this.save(items);
    else this.save(Object.assign({}, d, { items }));
    return items[idx];
  }

  remove(id) {
    const d = this.load();
    const items = Array.isArray(d) ? d : (d.items || []);
    const idx = items.findIndex(x => x.id === id);
    if (idx < 0) return false;
    items.splice(idx, 1);
    if (Array.isArray(d)) this.save(items);
    else this.save(Object.assign({}, d, { items }));
    return true;
  }
}

module.exports = { JSONStore, readJSON, writeJSON };
