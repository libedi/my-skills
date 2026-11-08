#!/usr/bin/env node
// Brainstorming board: a temporary local server that shows one round of questions
// in the browser and hands the answers back to the waiting agent.
// Node 18+ built-in modules only. See ../references/BOARD.md.

import http from 'node:http';
import { spawn } from 'node:child_process';
import { readFileSync, writeFileSync } from 'node:fs';
import { randomBytes } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const SCRIPT = fileURLToPath(import.meta.url);
const TEMPLATE = path.join(path.dirname(SCRIPT), '..', 'assets', 'board.html');
const HOLD_MS = 20000;
const WAITER_GRACE_MS = 5000;
const TYPES = new Set(['rate', 'choose', 'table', 'bucket', 'spectrum', 'text']);
const SCALES = new Set(['confirm', 'assumption', 'react', 'judge']);

const USAGE = `usage:
  node board.mjs start [--open] [--foreground] [--idle-minutes 30] [--port 0]
  node board.mjs ask <url> <round.json> [--timeout 540] [--out answer.json]
  node board.mjs wait <url> --round <id> [--timeout 540] [--out answer.json]
  node board.mjs handoff <url> --reason <text> [--next <text>]
  node board.mjs status <url>
  node board.mjs stop <url>
output flags: --ascii (escape non-ASCII in stdout) | --utf8 (plain UTF-8 stdout)`;
const BOOLEAN_FLAGS = new Set(['open', 'foreground', 'ascii', 'utf8']);

// Windows PowerShell 5.1 decodes a native command's stdout with the OEM code page
// (cp949 on Korean Windows), so UTF-8 Korean text arrives garbled. Escaping non-ASCII
// keeps stdout lossless there. Git Bash (MSYSTEM is set) reads UTF-8 correctly.
let asciiOut = process.platform === 'win32' && !process.env.MSYSTEM;

function parseArgs(argv) {
  const pos = [];
  const opt = {};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith('--')) {
      const key = a.slice(2);
      const next = argv[i + 1];
      if (BOOLEAN_FLAGS.has(key) || next === undefined || next.startsWith('--')) opt[key] = true;
      else { opt[key] = next; i++; }
    } else pos.push(a);
  }
  return { pos, opt };
}

function toJson(obj, pretty) {
  const text = JSON.stringify(obj, null, pretty ? 2 : 0);
  return asciiOut
    ? text.replace(/[\u007f-￿]/g, (c) => '\\u' + c.charCodeAt(0).toString(16).padStart(4, '0'))
    : text;
}

function out(obj, file) {
  if (file && file !== true) {
    writeFileSync(file, JSON.stringify(obj, null, 2) + '\n', 'utf8');
    process.stdout.write(toJson({ status: obj.status, round: obj.round, written: file }) + '\n');
  } else {
    process.stdout.write(toJson(obj, true) + '\n');
  }
}

function readText(file) {
  const buf = readFileSync(file);
  if (buf[0] === 0xff && buf[1] === 0xfe) return buf.subarray(2).toString('utf16le');
  if (buf[0] === 0xfe && buf[1] === 0xff) throw new Error('UTF-16BE is not supported. Save the file as UTF-8.');
  const text = buf.toString('utf8').replace(/^﻿/, '');
  if (text.includes('�')) throw new Error('the file is not valid UTF-8. Write it with a file tool as UTF-8, not with shell redirection.');
  return text;
}

function fail(message, extra = {}) {
  out({ status: 'error', message, ...extra });
  process.exit(1);
}

async function api(board, method, route, body, timeoutMs = 30000) {
  let base;
  try { base = new URL(board); } catch { fail(`invalid board url: ${board}`); }
  const target = new URL(route, base.origin);
  target.searchParams.set('t', base.searchParams.get('t') ?? '');
  const res = await fetch(target, {
    method,
    headers: body ? { 'content-type': 'application/json' } : undefined,
    body: body ? JSON.stringify(body) : undefined,
    signal: AbortSignal.timeout(timeoutMs),
  });
  const data = await res.json().catch(() => ({}));
  return { ok: res.ok, code: res.status, data };
}

function openBrowser(url) {
  const [cmd, args] = process.platform === 'win32'
    ? ['cmd', ['/c', 'start', '', url]]
    : process.platform === 'darwin' ? ['open', [url]] : ['xdg-open', [url]];
  try {
    const child = spawn(cmd, args, { detached: true, stdio: 'ignore', windowsHide: true });
    child.on('error', () => {});
    child.unref();
  } catch { /* best effort */ }
}

function validateRound(d) {
  const problems = [];
  const ids = new Set();
  if (!d || typeof d !== 'object' || Array.isArray(d)) return ['round must be a JSON object'];
  const addId = (id, where) => {
    if (!id || typeof id !== 'string') problems.push(`${where}: id is required`);
    else if (ids.has(id)) problems.push(`${where}: duplicate id ${id}`);
    else ids.add(id);
  };
  if (!Array.isArray(d.items) || d.items.length === 0) problems.push('items must be a non-empty array');
  let gates = 0;
  (Array.isArray(d.items) ? d.items : []).forEach((it, i) => {
    const w = `items[${i}]`;
    if (!it || typeof it !== 'object') { problems.push(`${w}: must be an object`); return; }
    if (!TYPES.has(it.type)) problems.push(`${w}: unknown type ${it.type}`);
    addId(it.id, w);
    if (it.type === 'rate' && it.scale !== undefined && !Array.isArray(it.scale) && !SCALES.has(it.scale)) {
      problems.push(`${w}: unknown scale ${it.scale}`);
    }
    if (it.type === 'choose' && (!Array.isArray(it.options) || it.options.length < 2)) {
      problems.push(`${w}: choose needs 2 or more options`);
    }
    if (it.type === 'table') {
      if (!Array.isArray(it.columns) || !Array.isArray(it.rows)) problems.push(`${w}: table needs columns and rows`);
      else it.rows.forEach((row, ri) => (Array.isArray(row) ? row : []).forEach((cell, ci) => {
        if (cell && typeof cell === 'object') {
          addId(cell.ask, `${w}.rows[${ri}][${ci}]`);
          if (!Array.isArray(cell.options) || cell.options.length < 2) problems.push(`${w}.rows[${ri}][${ci}]: ask needs 2 or more options`);
        }
      }));
    }
    if (it.type === 'bucket' && (!it.buckets || typeof it.buckets !== 'object' || !Array.isArray(it.entries))) {
      problems.push(`${w}: bucket needs buckets and entries`);
    }
    if (it.type === 'text' && it.gate) gates++;
  });
  if (gates > 1) problems.push('only one gate text item is allowed per round');
  if (d.history !== undefined && !Array.isArray(d.history)) problems.push('history must be an array');
  return problems;
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    let raw = '';
    req.setEncoding('utf8');
    req.on('data', (c) => { raw += c; if (raw.length > 1_000_000) reject(new Error('body too large')); });
    req.on('end', () => { try { resolve(raw ? JSON.parse(raw) : {}); } catch (e) { reject(e); } });
    req.on('error', reject);
  });
}

function send(res, code, obj) {
  if (res.writableEnded) return;
  res.writeHead(code, { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' });
  res.end(JSON.stringify(obj));
}

function serve(opt, onListen) {
  const token = String(opt.token ?? '');
  const idleMs = Number(opt['idle-minutes'] ?? 30) * 60000;
  const html = readFileSync(TEMPLATE, 'utf8');
  let seq = 0;
  let rev = 0;
  let round = null; // { id, data, state: 'asking' | 'answered' }
  let answer = null;
  let handoff = null;
  let waiters = [];
  let lastWaitAt = 0;
  let lastCliAt = Date.now();

  const waiting = () => waiters.length > 0 || Date.now() - lastWaitAt < WAITER_GRACE_MS;
  const phase = () => {
    if (handoff) return 'handoff';
    if (!round) return 'idle';
    if (round.state === 'answered') return 'processing';
    return waiting() ? 'asking' : 'detached';
  };
  const settle = (result) => {
    for (const w of waiters) { clearTimeout(w.timer); send(w.res, 200, result); }
    waiters = [];
    lastWaitAt = Date.now();
  };

  const server = http.createServer(async (req, res) => {
    const u = new URL(req.url, 'http://127.0.0.1');
    if (u.searchParams.get('t') !== token) return send(res, 403, { error: 'forbidden' });
    try {
      if (req.method === 'GET' && u.pathname === '/') {
        res.writeHead(200, { 'content-type': 'text/html; charset=utf-8', 'cache-control': 'no-store' });
        return res.end(html);
      }
      if (req.method === 'GET' && u.pathname === '/api/state') {
        return send(res, 200, { phase: phase(), rev, round: round && { id: round.id, data: round.data }, handoff });
      }
      if (req.method === 'POST' && u.pathname === '/api/answer') {
        const body = await readBody(req);
        if (!round || round.id !== body.round || round.state !== 'asking') return send(res, 409, { error: 'stale' });
        if (!waiting()) return send(res, 409, { error: 'not-waiting' });
        lastCliAt = Date.now();
        round.state = 'answered';
        answer = {
          status: body.kind === 'exit' ? 'exit' : 'answered',
          round: round.id,
          answers: body.answers ?? {},
          pending: body.pending ?? [],
          reopen: body.reopen ?? [],
          memo: body.memo ?? '',
        };
        rev++;
        settle(answer);
        return send(res, 200, { ok: true });
      }

      lastCliAt = Date.now();
      if (req.method === 'POST' && u.pathname === '/api/round') {
        const data = await readBody(req);
        if (round && round.state === 'asking') settle({ status: 'cancelled', round: round.id });
        round = { id: `r${++seq}`, data, state: 'asking' };
        answer = null;
        handoff = null;
        lastWaitAt = Date.now();
        rev++;
        return send(res, 200, { round: round.id });
      }
      if (req.method === 'GET' && u.pathname === '/api/wait') {
        const id = u.searchParams.get('round');
        if (!round || round.id !== id) return send(res, 200, { status: 'stale', round: id, current: round?.id ?? null });
        if (round.state === 'answered') return send(res, 200, answer);
        const hold = Math.max(1000, Math.min(HOLD_MS, Number(u.searchParams.get('hold')) || HOLD_MS));
        const w = { res };
        w.timer = setTimeout(() => {
          waiters = waiters.filter((x) => x !== w);
          lastWaitAt = Date.now();
          send(res, 200, { status: 'pending', round: id });
        }, hold);
        res.on('close', () => {
          if (waiters.includes(w)) {
            clearTimeout(w.timer);
            waiters = waiters.filter((x) => x !== w);
            lastWaitAt = Date.now();
          }
        });
        waiters.push(w);
        lastWaitAt = Date.now();
        return;
      }
      if (req.method === 'POST' && u.pathname === '/api/handoff') {
        const body = await readBody(req);
        if (round && round.state === 'asking') settle({ status: 'cancelled', round: round.id });
        round = null;
        answer = null;
        handoff = { reason: String(body.reason ?? ''), next: String(body.next ?? '') };
        rev++;
        return send(res, 200, { ok: true });
      }
      if (req.method === 'GET' && u.pathname === '/api/status') {
        return send(res, 200, { phase: phase(), round: round?.id ?? null, waiting: round?.state === 'asking' && waiting() });
      }
      if (req.method === 'POST' && u.pathname === '/api/stop') {
        settle({ status: 'stopped', round: round?.id ?? null });
        send(res, 200, { ok: true });
        setTimeout(() => process.exit(0), 100);
        return;
      }
      return send(res, 404, { error: 'not found' });
    } catch (e) {
      return send(res, 400, { error: String(e?.message ?? e) });
    }
  });

  process.stdout.on('error', () => {});
  server.listen(Number(opt.port ?? 0) || 0, '127.0.0.1', () => {
    const { port } = server.address();
    if (onListen) onListen(port);
    else process.stdout.write(JSON.stringify({ port }) + '\n');
  });
  setInterval(() => {
    if (waiters.length === 0 && Date.now() - lastCliAt > idleMs) process.exit(0);
  }, 15000);
}

async function start(opt) {
  const token = randomBytes(16).toString('hex');
  if (opt.foreground) {
    // Fallback for hosts that kill background processes when a command ends:
    // run this in its own terminal and keep it open.
    return serve({ token, 'idle-minutes': opt['idle-minutes'], port: opt.port === true ? undefined : opt.port }, (port) => {
      const url = `http://127.0.0.1:${port}/?t=${token}`;
      if (opt.open) openBrowser(url);
      out({ status: 'started', url, pid: process.pid, foreground: true });
    });
  }
  const args = [SCRIPT, 'serve', '--token', token, '--idle-minutes', String(opt['idle-minutes'] ?? 30)];
  if (opt.port && opt.port !== true) args.push('--port', String(opt.port));
  const child = spawn(process.execPath, args, { detached: true, stdio: ['ignore', 'pipe', 'ignore'], windowsHide: true });
  let line;
  try {
    line = await new Promise((resolve, reject) => {
      let buf = '';
      const timer = setTimeout(() => reject(new Error('server did not start within 10s')), 10000);
      child.stdout.setEncoding('utf8');
      child.stdout.on('data', (chunk) => {
        buf += chunk;
        const i = buf.indexOf('\n');
        if (i >= 0) { clearTimeout(timer); resolve(buf.slice(0, i)); }
      });
      child.on('error', (e) => { clearTimeout(timer); reject(e); });
      child.on('exit', (code) => { clearTimeout(timer); reject(new Error(`server exited with code ${code}`)); });
    });
  } catch (e) {
    fail(`could not start board: ${e.message}`);
  }
  child.removeAllListeners('exit');
  child.stdout.destroy();
  child.unref();
  const { port } = JSON.parse(line);
  const url = `http://127.0.0.1:${port}/?t=${token}`;
  if (opt.open) openBrowser(url);
  out({ status: 'started', url, pid: child.pid });
}

async function waitLoop(board, id, opt) {
  const until = Date.now() + Number(opt.timeout ?? 540) * 1000;
  while (Date.now() < until) {
    const hold = Math.min(HOLD_MS, Math.max(1000, until - Date.now()));
    let r;
    try {
      r = await api(board, 'GET', `/api/wait?round=${encodeURIComponent(id)}&hold=${hold}`, null, hold + 10000);
    } catch (e) {
      return fail(`board unreachable: ${e.message}`, { round: id });
    }
    if (!r.ok) return fail(`board error (${r.code})`, { round: id, ...r.data });
    if (r.data.status !== 'pending') return out(r.data, opt.out);
  }
  out({ status: 'timeout', round: id, hint: 'The question is still on the board. Run wait again to keep waiting.' }, opt.out);
}

async function main() {
  const [cmd, ...rest] = process.argv.slice(2);
  const { pos, opt } = parseArgs(rest);
  if (opt.ascii) asciiOut = true;
  if (opt.utf8) asciiOut = false;
  switch (cmd) {
    case 'serve':
      return serve(opt);
    case 'start':
      return start(opt);
    case 'ask': {
      const [board, file] = pos;
      if (!board || !file) return fail(USAGE);
      let data;
      try {
        data = JSON.parse(readText(file));
      } catch (e) {
        return fail(`could not read round JSON: ${e.message}`);
      }
      const problems = validateRound(data);
      if (problems.length) return fail('invalid round', { problems });
      let r;
      try { r = await api(board, 'POST', '/api/round', data); } catch (e) { return fail(`board unreachable: ${e.message}`); }
      if (!r.ok) return fail(`board rejected round (${r.code})`, r.data);
      return waitLoop(board, r.data.round, opt);
    }
    case 'wait': {
      const [board] = pos;
      if (!board || !opt.round || opt.round === true) return fail(USAGE);
      return waitLoop(board, String(opt.round), opt);
    }
    case 'handoff': {
      const [board] = pos;
      if (!board || !opt.reason || opt.reason === true) return fail(USAGE);
      try {
        const r = await api(board, 'POST', '/api/handoff', { reason: opt.reason, next: opt.next === true ? '' : opt.next ?? '' });
        return r.ok ? out({ status: 'handed-off' }) : fail(`board error (${r.code})`, r.data);
      } catch (e) { return fail(`board unreachable: ${e.message}`); }
    }
    case 'status': {
      const [board] = pos;
      if (!board) return fail(USAGE);
      try {
        const r = await api(board, 'GET', '/api/status', null, 5000);
        return r.ok ? out({ status: 'running', ...r.data }) : fail(`board error (${r.code})`, r.data);
      } catch { return out({ status: 'not-running' }); }
    }
    case 'stop': {
      const [board] = pos;
      if (!board) return fail(USAGE);
      try { await api(board, 'POST', '/api/stop', {}, 5000); } catch { /* already gone */ }
      return out({ status: 'stopped' });
    }
    default:
      return fail(USAGE);
  }
}

main();
