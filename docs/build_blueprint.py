#!/usr/bin/env python3
"""
build_blueprint.py — generates Vault_Mobile_Blueprint.odt (OpenDocument Text)
with NO external dependencies. An .odt is just a ZIP of XML parts, so we build it
by hand. Open the result in LibreOffice Writer (or any OpenDocument reader).

This is the LINE-LEVEL CODE BLUEPRINT for pass-manager-mobile: an annotated
source listing. It reproduces the ACTUAL code of every file in chunks, with
terse line-keyed notes, plus the REAL DATA the app uses (the localStorage JSON,
the OOXML the export emits, the agile-encryption byte layout, the CFB header
map, the verified generation vectors). Theory is kept to a minimum.

Companion document: Vault_Mobile_Documentation.odt (the what/why/how-to-use/deploy
reference) — built by build_docs.py.

Regenerate:  python3 docs/build_blueprint.py
"""
import html
import re
import zipfile
import os

parts = []  # accumulates the document body XML

# ---------------------------------------------------------------------------
# Inline / block helpers  (same proven machinery as build_docs.py)
# ---------------------------------------------------------------------------
def esc(s):
    return html.escape(s, quote=False)

_INLINE = re.compile(r'`([^`]+)`|\*\*([^*]+)\*\*')

def inline(s):
    out, pos = [], 0
    for m in _INLINE.finditer(s):
        out.append(esc(s[pos:m.start()]))
        if m.group(1) is not None:
            out.append(f'<text:span text:style-name="Mono">{esc(m.group(1))}</text:span>')
        else:
            out.append(f'<text:span text:style-name="Bold">{esc(m.group(2))}</text:span>')
        pos = m.end()
    out.append(esc(s[pos:]))
    return ''.join(out)

def title(t):
    parts.append(f'<text:p text:style-name="DocTitle">{esc(t)}</text:p>')

def subtitle(t):
    parts.append(f'<text:p text:style-name="DocSubtitle">{esc(t)}</text:p>')

def h(level, t):
    parts.append(f'<text:h text:style-name="Heading_20_{level}" '
                 f'text:outline-level="{level}">{inline(t)}</text:h>')

def p(t, style="Standard"):
    parts.append(f'<text:p text:style-name="{style}">{inline(t)}</text:p>')

def spacer():
    parts.append('<text:p text:style-name="Standard"/>')

def _code_line(line):
    line = line.replace('\t', '    ')
    out, j, n = [], 0, len(line)
    while j < n:
        if line[j] == ' ':
            k = j
            while k < n and line[k] == ' ':
                k += 1
            run = k - j
            out.append(' ' if run == 1 else f'<text:s text:c="{run}"/>')
            j = k
        else:
            k = j
            while k < n and line[k] != ' ':
                k += 1
            out.append(esc(line[j:k]))
            j = k
    return ''.join(out)

def code(block):
    for line in block.split('\n'):
        if line == '':
            parts.append('<text:p text:style-name="Code"/>')
        else:
            parts.append(f'<text:p text:style-name="Code">{_code_line(line)}</text:p>')

def bullets(items):
    parts.append('<text:list text:style-name="Bullets">')
    for it in items:
        parts.append('<text:list-item>'
                     f'<text:p text:style-name="ListItem">{inline(it)}</text:p>'
                     '</text:list-item>')
    parts.append('</text:list>')

def numbers(items):
    parts.append('<text:list text:style-name="Numbers">')
    for it in items:
        parts.append('<text:list-item>'
                     f'<text:p text:style-name="ListItem">{inline(it)}</text:p>'
                     '</text:list-item>')
    parts.append('</text:list>')

_tbl_count = [0]

def table(headers, rows):
    _tbl_count[0] += 1
    name = f"T{_tbl_count[0]}"
    ncol = len(headers)
    parts.append(f'<table:table table:name="{name}" table:style-name="Tbl">')
    for _ in range(ncol):
        parts.append('<table:table-column table:style-name="Tbl.col"/>')
    parts.append('<table:table-row>')
    for hd in headers:
        parts.append('<table:table-cell table:style-name="Tbl.hcell" office:value-type="string">'
                     f'<text:p text:style-name="TblHead">{inline(hd)}</text:p></table:table-cell>')
    parts.append('</table:table-row>')
    for row in rows:
        parts.append('<table:table-row>')
        for cell in row:
            parts.append('<table:table-cell table:style-name="Tbl.cell" office:value-type="string">'
                         f'<text:p text:style-name="TblCell">{inline(cell)}</text:p></table:table-cell>')
        parts.append('</table:table-row>')
    parts.append('</table:table>')

def pagebreak():
    parts.append('<text:p text:style-name="PageBreak"/>')

# convenience captions
def src(caption):
    """A small caption above a verbatim code block, e.g. SOURCE — derivePassword (crypto.js:150-176)."""
    p("**SOURCE — " + caption + "**")

def data(caption):
    p("**REAL DATA — " + caption + "**")

def notes(items):
    bullets(items)

# ===========================================================================
#  DOCUMENT CONTENT — annotated source + real data
# ===========================================================================
title("Vault Mobile — Code Blueprint (annotated source)")
subtitle("pass-manager-mobile · every file, every function, verbatim code + real data · v2.0 · 2026-06-30")

p("This is an **annotated source listing** of the `pass-manager-mobile` app. It "
  "reproduces the **actual code** of each file in chunks, each followed by terse "
  "line-keyed notes, and shows the **real data** the code produces and consumes — the "
  "`localStorage` JSON, the spreadsheet XML, the encryption byte layout, the file "
  "format maps and the verified generation vectors. Read a `SOURCE` block as the exact "
  "lines in the file; read a `REAL DATA` block as a concrete artifact.")
p("References like `crypto.js:150` mean file `js/crypto.js`, line 150. Line numbers "
  "match the merged `main` / `documento` branch (the complete app, export included). "
  "Code is verbatim; a few over-long lines are wrapped to fit the page. For the "
  "narrative \"what is this / how do I deploy it\", see `Vault_Mobile_Documentation.odt`.")

# ---- Contents ----
h(1, "Contents")
numbers([
    "Orientation (globals, load order, where state lives) — 1 page",
    "index.html — verbatim markup + the id→handler contract",
    "css/style.css + fonts.css — the real rules",
    "manifest.webmanifest — the real JSON",
    "sw.js — the whole file, annotated",
    "crypto.js — the whole engine, annotated + charset/vector data",
    "store.js — the whole data layer, annotated + the localStorage JSON",
    "export.js — the whole export, annotated + OOXML/agile/CFB data",
    "app.js — the whole controller, annotated + the rendered HTML",
    "manual.js — structure + the wiring",
    "End-to-end call chains (exact functions + lines)",
    "Consolidated data reference (schemas + artifacts)",
    "Appendix — function index (every function → file:line)",
])

# ===========================================================================
pagebreak()
h(1, "1. Orientation")
h(2, "1.1 The four globals (IIFE pattern)")
p("No bundler. Each library file runs an IIFE and assigns ONE global; everything else "
  "is closure-private. The same shape ends every library file:")
src("the IIFE/global pattern (crypto.js:17 & 246-256, mirrored in store.js, export.js)")
code('''const PMCrypto = (function () {
  // ...private state + helpers...
  return { derivePassword, hashMaster, verifyMaster, /* ...public API... */ };
})();
// Node-only line: lets the same file be unit-tested off-browser (harmless in the browser)
if (typeof module !== "undefined" && module.exports) module.exports = PMCrypto;''')
table(
    ["Global", "File", "Public surface (the returned object)"],
    [
        ["PMCrypto", "crypto.js", "derivePassword, hashMaster, verifyMaster, deriveAesKey, "
                                  "encryptJSON, decryptJSON, randomBytes, bytesToHex, hexToBytes, b64, unb64, hasSubtle"],
        ["PMStore", "store.js", "isInitialised, isUnlocked, getIterations, createMaster, unlock, lock, "
                                "hasExportPassword, verifyExportPassword, setExportPassword, getMaster, listEntries, "
                                "getEntry, exists, insertEntry, updateEntryPassword, setWhereUsed, setNeedsUpdate, "
                                "deleteEntry, exportSnapshot, mergeSnapshot, wipeEverything"],
        ["PMExport", "export.js", "buildEncryptedXlsx, entriesToRows, _buildXlsx, _buildCFB"],
        ["MANUAL_HTML", "manual.js", "a single HTML string (the manual)"],
    ],
)
h(2, "1.2 Load order (index.html:182-186)")
code('''<script src="js/crypto.js"></script>   <!-- defines PMCrypto -->
<script src="js/store.js"></script>    <!-- uses PMCrypto -->
<script src="js/export.js"></script>   <!-- defines PMExport -->
<script src="js/manual.js"></script>   <!-- defines MANUAL_HTML -->
<script src="js/app.js"></script>      <!-- uses all of the above; ends with route() -->''')
h(2, "1.3 Where every secret/value lives")
table(
    ["Value", "At rest (localStorage)", "In memory (while unlocked)"],
    [
        ["phrase", "— never —", "a DOM input for a moment, then cleared"],
        ["master password", "only PBKDF2 verifier (`master_verifier`)", "`store.js` `_master`"],
        ["export password", "only PBKDF2 verifier (`export_verifier`)", "— never held —"],
        ["vault AES key", "— never —", "`store.js` `_aesKey` (CryptoKey)"],
        ["entries (plaintext)", "— never —", "`store.js` `_entries`"],
        ["entries (ciphertext)", "`pm_vault` = `b64(iv):b64(ct)`", "—"],
        ["salts / iterations", "`pm_meta` (hex JSON)", "—"],
    ],
)
p("`lock()` nulls `_master`, `_aesKey`, `_entries`. Closing the tab does the same "
  "(memory is gone). Nothing secret survives a lock.")

# ===========================================================================
pagebreak()
h(1, "2. index.html — markup + the id→handler contract")
p("One page. Three `<section class>` screens and four `<div class=\"modal\">` dialogs, "
  "all in the DOM at once; visibility is the `hidden` attribute. `app.js` binds "
  "everything by `id`. Verbatim markup of each unit follows.")

h(2, "2.1 Head + PWA wiring (index.html:1-16)")
code('''<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover, maximum-scale=1.0, user-scalable=no">
<meta name="theme-color" content="#0a0d12">
<meta name="apple-mobile-web-app-capable" content="yes">
<link rel="manifest" href="manifest.webmanifest">
<link rel="apple-touch-icon" href="icons/icon-192.png">
<link rel="stylesheet" href="css/fonts.css">
<link rel="stylesheet" href="css/style.css">''')
notes([
    "fixed viewport, no user zoom → app-like.",
    "`theme-color`/apple meta → native feel when installed.",
    "manifest link enables Install; fonts.css before style.css.",
])

h(2, "2.2 Setup screen (index.html:20-39)")
code('''<section id="screen-setup" class="lock-wrap" hidden>
  <div class="lock-card">
    <h1>Create your master password</h1>
    <form id="setup-form">
      <input type="password" id="setup-master"  required minlength="6" autocomplete="new-password">
      <input type="password" id="setup-confirm" required minlength="6" autocomplete="new-password">
      <div class="error" id="setup-error"></div>
      <button type="submit" class="btn-primary">Create vault →</button>
    </form>
    <a class="manual-link" href="#" id="setup-manual-link">Read the manual</a>
  </div>
</section>''')

h(2, "2.3 Unlock screen (index.html:41-55)")
code('''<section id="screen-unlock" class="lock-wrap" hidden>
  <form id="unlock-form">
    <input type="password" id="unlock-master" required autocomplete="current-password">
    <div class="error" id="unlock-error"></div>
    <button type="submit" class="btn-primary">Unlock →</button>
  </form>
  <a class="manual-link" href="#" id="unlock-manual-link">Read the manual</a>
</section>''')

h(2, "2.4 App screen: top bar + generator + vault (index.html:57-116)")
code('''<header class="topbar">
  <nav>
    <a href="#" class="nav-link" id="nav-export">⤓ Export</a>
    <a href="#" class="nav-link" id="nav-manual">Manual</a>
    <a href="#" class="nav-link lock-btn" id="nav-lock">Lock ⤬</a>
  </nav>
</header>
<!-- generator -->
<input id="phrase" type="password" ...>
<label class="reveal-row"><input type="checkbox" id="show-phrase"> show phrase</label>
<input id="site" type="text" ...>
<input id="username" type="text" ...>
<input id="length" type="range" min="8" max="64" value="20">  <span id="len-val">20</span>
<textarea id="where_used" rows="2"></textarea>
<div class="preview-box" id="preview-box" hidden><code id="preview-pass"></code></div>
<button class="btn-ghost"   id="btn-preview">Preview</button>
<button class="btn-primary" id="btn-save">Generate &amp; Save →</button>
<div class="form-msg" id="gen-msg"></div>
<!-- vault -->
<input id="search" class="search" type="text" placeholder="Search…">
<div id="vault-list" class="vault-list"></div>''')

h(2, "2.5 The four dialogs (index.html:127-180)")
code('''<div class="modal" id="rotate-modal" hidden>
  <p id="rotate-target"></p>
  <input type="password" id="rotate-phrase">
  <div class="form-msg" id="rotate-msg"></div>
  <button id="rotate-cancel">Cancel</button> <button id="rotate-go">Rotate →</button>
</div>

<div class="modal" id="export-setup-modal" hidden>          <!-- set the 2nd password -->
  <h3 id="export-setup-title">Create your export password</h3>
  <p  id="export-setup-note">...re-labelled at runtime for create vs set...</p>
  <input type="password" id="export-setup-pass"    minlength="6">
  <input type="password" id="export-setup-confirm" minlength="6">
  <div class="form-msg" id="export-setup-msg"></div>
  <button id="export-setup-cancel">Back</button> <button id="export-setup-go">Create vault →</button>
</div>

<div class="modal" id="export-verify-modal" hidden>         <!-- enter 2nd pw to export -->
  <input type="password" id="export-verify-pass">
  <div class="form-msg" id="export-verify-msg"></div>
  <button id="export-verify-cancel">Cancel</button> <button id="export-verify-go">Export →</button>
</div>

<div class="toast" id="toast" hidden></div>''')

h(2, "2.6 The id → app.js binding table (the contract)")
table(
    ["Element id", "Bound at (app.js)", "Action"],
    [
        ["#setup-form submit", "46", "validate master → openExportSetup('create')"],
        ["#unlock-form submit", "64", "PMStore.unlock → route()"],
        ["#nav-lock / #nav-manual", "78 / 79", "lock+route / open manual"],
        ["#btn-preview / #btn-save", "102 / 114", "derive (no save) / derive + insertEntry"],
        ["#search", "250", "renderVault() filter"],
        ["#rotate-go", "267", "derive rev+1 → updateEntryPassword"],
        ["#export-setup-go", "315", "create vault OR setExportPassword+export"],
        ["#nav-export", "338", "4 guards → openExportVerify / openExportSetup('set')"],
        ["#export-verify-go", "356", "verifyExportPassword → doExport()"],
    ],
)

# ===========================================================================
pagebreak()
h(1, "3. css/style.css + fonts.css — the real rules")
h(2, "3.1 Design tokens (style.css:1-16)")
code(''':root {
  --bg:#0a0d12; --bg-2:#0e131a; --panel:#121821; --panel-2:#161d28; --line:#232c39;
  --text:#e8edf4; --muted:#8a97a8; --accent:#1ea7ff; --accent-2:#0f6fd6;
  --yellow:#f4d35e; --yellow-bg:#3a3417; --danger:#ff5d6c; --radius:14px;
  --mono:'JetBrains Mono', ui-monospace, monospace;
}''')
h(2, "3.2 The three rules that make the UI work (style.css:18-32, 79-89, 158-161)")
code('''* { box-sizing: border-box; }
[hidden] { display: none !important; }                 /* screen/modal toggling depends on this */

label { display:block; font-size:13px; margin:14px 0 6px; color:#cdd6e2; }
input[type=text], input[type=password], textarea, .search {
  width:100%; background:var(--bg); border:1px solid var(--line); color:var(--text);
  border-radius:10px; padding:13px; font-size:16px;   /* 16px stops iOS/Android focus-zoom */
}
.entry.flagged .notes-box { background:var(--yellow-bg); border-color:var(--yellow); color:#fff4cf; }
.entry.flagged { border-color: rgba(244,211,94,0.45); }''')
notes([
    "`[hidden]{display:none !important}` (L20) beats `.modal{display:flex}` (L191) — without "
    "it, dialogs could never hide.",
    "input `font-size:16px` (L85) suppresses mobile focus auto-zoom.",
    "`.entry.flagged` is the yellow 'needs updating' state applied by app.js after a rotate.",
])
h(2, "3.3 Vault card + modal + toast (style.css:126-208, selected)")
code('''.entry { background:var(--panel-2); border:1px solid var(--line); border-radius:12px; padding:16px; }
.pass-val { font-family:var(--mono); flex:1; background:var(--bg); border:1px solid var(--line);
            border-radius:8px; padding:11px 12px; cursor:pointer; word-break:break-all; letter-spacing:1px; }
.rev-badge { background:rgba(30,167,255,.12); color:var(--accent); border:1px solid rgba(30,167,255,.3);
             border-radius:6px; padding:1px 7px; font-family:var(--mono); }
.modal { position:fixed; inset:0; z-index:50; background:rgba(5,7,10,.7); backdrop-filter:blur(4px);
         display:flex; align-items:center; justify-content:center; }
.toast { position:fixed; bottom:calc(24px + env(safe-area-inset-bottom)); left:50%;
         transform:translateX(-50%); border:1px solid var(--accent); z-index:100; }''')
h(2, "3.4 fonts.css — zero external calls (fonts.css:5-19)")
code('''@font-face { font-family:'Inter'; font-weight:100 900; font-display:swap;
             src:url('../fonts/inter.woff2') format('woff2'); }
@font-face { font-family:'JetBrains Mono'; font-weight:100 800; font-display:swap;
             src:url('../fonts/jetbrains-mono.woff2') format('woff2'); }''')
p("Two **variable** woff2 files (one weight axis each) load from the repo — no Google "
  "Fonts request, identical offline.")

# ===========================================================================
h(1, "4. manifest.webmanifest — the real JSON (verbatim)")
code('''{
  "name": "Vault — Password Manager",
  "short_name": "Vault",
  "description": "Deterministic, offline password generator & manager.",
  "start_url": ".",
  "scope": ".",
  "display": "standalone",
  "orientation": "portrait",
  "background_color": "#0a0d12",
  "theme_color": "#0a0d12",
  "icons": [
    { "src": "icons/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any" },
    { "src": "icons/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any" },
    { "src": "icons/icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable" }
  ]
}''')
notes([
    "`start_url`/`scope` = `\".\"` (relative) → works under a Pages sub-path `/<repo>/`.",
    "`display:standalone` + portrait → full-screen launch; dark colors → no white flash.",
    "maskable icon → clean Android adaptive-icon crop.",
])

# ===========================================================================
pagebreak()
h(1, "5. sw.js — the whole service worker (62 lines)")
h(2, "5.1 Constants (sw.js:7-24)")
code('''const CACHE_VERSION = "vault-v3";   // BUMP whenever any cached file changes
const ASSETS = [
  ".", "index.html", "manifest.webmanifest",
  "css/fonts.css", "css/style.css",
  "fonts/inter.woff2", "fonts/jetbrains-mono.woff2",
  "js/crypto.js", "js/store.js", "js/export.js", "js/manual.js", "js/app.js",
  "icons/icon-192.png", "icons/icon-512.png", "icons/icon-maskable-512.png",
];''')
h(2, "5.2 install / activate (sw.js:27-40)")
code('''self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_VERSION).then((cache) => cache.addAll(ASSETS)).then(() => self.skipWaiting())
  );
});
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_VERSION).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});''')
notes([
    "install: pre-cache the whole shell, then `skipWaiting()` (new worker activates immediately).",
    "activate: delete every cache key ≠ current `CACHE_VERSION`, then `clients.claim()`.",
])
h(2, "5.3 fetch — cache-first (sw.js:44-62)")
code('''self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;
  event.respondWith(
    caches.match(req).then((cached) => {
      if (cached) return cached;                       // offline-first
      return fetch(req)
        .then((res) => {
          if (res && res.status === 200 && new URL(req.url).origin === self.location.origin) {
            const copy = res.clone();
            caches.open(CACHE_VERSION).then((c) => c.put(req, copy));   // opportunistic cache
          }
          return res;
        })
        .catch(() => cached);                          // network failed → whatever we had
    })
  );
});''')

# ===========================================================================
pagebreak()
h(1, "6. crypto.js — the engine (the whole file, annotated)")
p("Faithful JS port of desktop `core/crypto.py`. The rule: `derivePassword(...)` must "
  "equal Python byte-for-byte. Native Web Crypto when available, pure-JS fallback "
  "otherwise.")

h(2, "6.1 Character classes (crypto.js:19-25)")
src("the charsets (crypto.js:19-25)")
code('''const UPPER   = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
const LOWER   = "abcdefghijklmnopqrstuvwxyz";
const DIGIT   = "0123456789";
const SPECIAL = "!@#$%^&*()-_=+[]{};:,.?";
const FULL    = UPPER + LOWER + DIGIT + SPECIAL;
const CLASSES = [UPPER, LOWER, DIGIT, SPECIAL];
const enc = new TextEncoder();''')
data("the FULL set, expanded (this is the exact alphabet of every password)")
code('''FULL =
"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()-_=+[]{};:,.?"

lengths:  UPPER 26 + LOWER 26 + DIGIT 10 + SPECIAL 23  =  85 characters
excluded on purpose: quote ' "  backslash \\  space  backtick `  (they break shells/CSVs/forms)''')
notes([
    "Order is fixed — reordering would change every output. `CLASSES` drives the "
    "forced-one-of-each step in derivePassword.",
])

h(2, "6.2 Pure-JS SHA-256 (crypto.js:30-85) — the fallback hash")
src("round constants + sha256 (crypto.js:30-85)")
code('''const K = new Uint32Array([
  0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
  /* ... 64 standard SHA-256 constants ... */
  0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
]);
const rotr = (x, n) => (x >>> n) | (x << (32 - n));

function sha256(msg) {
  let h0=0x6a09e667,h1=0xbb67ae85,h2=0x3c6ef372,h3=0xa54ff53a,
      h4=0x510e527f,h5=0x9b05688c,h6=0x1f83d9ab,h7=0x5be0cd19;
  const l = msg.length, bitLen = l*8, withOne = l+1;
  const pad = (56 - (withOne % 64) + 64) % 64;          // pad to 56 mod 64
  const total = withOne + pad + 8;
  const buf = new Uint8Array(total); buf.set(msg,0); buf[l]=0x80;   // append 0x80
  const dv = new DataView(buf.buffer);
  dv.setUint32(total-4, bitLen >>> 0, false);           // 64-bit big-endian length
  dv.setUint32(total-8, Math.floor(bitLen/0x100000000), false);
  const w = new Uint32Array(64);
  for (let i=0; i<total; i+=64) {                        // per 512-bit block
    for (let t=0;t<16;t++) w[t]=dv.getUint32(i+t*4,false);
    for (let t=16;t<64;t++){                             // message schedule
      const s0=rotr(w[t-15],7)^rotr(w[t-15],18)^(w[t-15]>>>3);
      const s1=rotr(w[t-2],17)^rotr(w[t-2],19)^(w[t-2]>>>10);
      w[t]=(w[t-16]+s0+w[t-7]+s1)|0;
    }
    let a=h0,b=h1,c=h2,d=h3,e=h4,f=h5,g=h6,h=h7;
    for (let t=0;t<64;t++){                              // 64 compression rounds
      const S1=rotr(e,6)^rotr(e,11)^rotr(e,25), ch=(e&f)^(~e&g);
      const t1=(h+S1+ch+K[t]+w[t])|0;
      const S0=rotr(a,2)^rotr(a,13)^rotr(a,22), maj=(a&b)^(a&c)^(b&c);
      const t2=(S0+maj)|0;
      h=g;g=f;f=e;e=(d+t1)|0; d=c;c=b;b=a;a=(t1+t2)|0;
    }
    h0=(h0+a)|0;h1=(h1+b)|0;h2=(h2+c)|0;h3=(h3+d)|0;
    h4=(h4+e)|0;h5=(h5+f)|0;h6=(h6+g)|0;h7=(h7+h)|0;
  }
  const out=new Uint8Array(32), odv=new DataView(out.buffer);
  [h0,h1,h2,h3,h4,h5,h6,h7].forEach((hh,i)=>odv.setUint32(i*4,hh>>>0,false));
  return out;
}''')
notes([
    "Textbook SHA-256: pad → 0x80 → 64-bit BE length; 16-word load, 48-word schedule, 64 rounds.",
    "`|0` / `>>> 0` keep arithmetic in 32-bit. Only used when `crypto.subtle` is absent.",
])

h(2, "6.3 HMAC + pure PBKDF2 (crypto.js:87-128)")
src("hmacSha256 + pbkdf2Pure (crypto.js:87-128)")
code('''function concat(a,b){ const o=new Uint8Array(a.length+b.length); o.set(a,0); o.set(b,a.length); return o; }

function hmacSha256(key, msg) {
  const block = 64; let k = key;
  if (k.length > block) k = sha256(k);
  if (k.length < block) { const t=new Uint8Array(block); t.set(k); k=t; }
  const okey=new Uint8Array(block), ikey=new Uint8Array(block);
  for (let i=0;i<block;i++){ okey[i]=k[i]^0x5c; ikey[i]=k[i]^0x36; }
  return sha256(concat(okey, sha256(concat(ikey, msg))));     // H(okey ‖ H(ikey ‖ msg))
}

function pbkdf2Pure(pw, salt, iterations, dklen) {
  const hLen = 32, blocks = Math.ceil(dklen/hLen);
  const out = new Uint8Array(blocks*hLen);
  for (let i=1;i<=blocks;i++){
    const intBlock=new Uint8Array(4); new DataView(intBlock.buffer).setUint32(0,i,false);
    let u=hmacSha256(pw, concat(salt,intBlock));     // U1 = PRF(pw, salt‖INT(i))
    const t=u.slice();
    for (let j=1;j<iterations;j++){ u=hmacSha256(pw,u); for(let k=0;k<hLen;k++) t[k]^=u[k]; }  // XOR all U
    out.set(t,(i-1)*hLen);
  }
  return out.slice(0,dklen);
}''')
notes([
    "Standard HMAC (ipad 0x36 / opad 0x5c) and standard PBKDF2 (T_i = ⊕ U_j). Identical math to the native path.",
])

h(2, "6.4 PBKDF2 dispatcher (crypto.js:133-145)")
src("pbkdf2 — native if possible (crypto.js:133-145)")
code('''async function pbkdf2(secretStr, saltBytes, iterations, dklen) {
  const pw = enc.encode(secretStr);
  const subtle = globalThis.crypto && globalThis.crypto.subtle;
  if (subtle) {                                              // FAST: native Web Crypto
    const km = await subtle.importKey("raw", pw, { name:"PBKDF2" }, false, ["deriveBits"]);
    const bits = await subtle.deriveBits(
      { name:"PBKDF2", salt:saltBytes, iterations, hash:"SHA-256" }, km, dklen*8);
    return new Uint8Array(bits);
  }
  return pbkdf2Pure(pw, saltBytes, iterations, dklen);       // FALLBACK: pure JS
}''')

h(2, "6.5 derivePassword — THE generator (crypto.js:150-176)")
src("derivePassword (crypto.js:150-176)")
code('''async function derivePassword(phrase, site, revision, length, iterations) {
  if (length < 8) length = 8;                                                   // L150
  const normalisedSite = String(site).trim().toLowerCase();                     // L152
  const salt = enc.encode(`pwgen|v1|${normalisedSite}|rev${parseInt(revision,10)}`);  // L153
  const dklen = length + 8;                                                     // L154
  const dk = await pbkdf2(phrase, salt, iterations, dklen);                     // L155

  const out = new Array(length);
  for (let i=0;i<length;i++) out[i] = FULL[dk[i] % FULL.length];                // L158  map byte→char

  const perm = new Array(length);
  for (let i=0;i<length;i++) perm[i]=i;                                         // identity
  for (let i=length-1;i>0;i--){                                                 // seeded Fisher-Yates
    const k = dk[(i*7) % dklen] % (i+1);                                        // L163  swap idx from bytes
    const tmp=perm[i]; perm[i]=perm[k]; perm[k]=tmp;
  }

  const extra = dk.slice(length, length+8);                                     // L169  8 spare bytes
  for (let idx=0; idx<CLASSES.length; idx++){                                   // force 1 of each class
    const cls = CLASSES[idx];
    const pos = perm[idx];                                                      // into a shuffled slot
    out[pos] = cls[extra[idx] % cls.length];                                    // L173
  }
  return out.join("");                                                          // L175
}''')
notes([
    "L152 trim+lower → `Gmail`/`gmail`/`' gmail '` collide.",
    "L153 salt grammar `pwgen|v1|<site>|rev<n>` bakes in site+revision (change either ⇒ all bytes change).",
    "L155 PBKDF2 → `length+8` bytes; first `length` map to chars, last 8 force the classes.",
    "L163 the shuffle indices are themselves derived bytes → deterministic, not random.",
    "L173 forces one Upper/Lower/Digit/Special into the first four PERMUTED positions ⇒ complexity always passes.",
])
data("verified vectors — phrase | site | rev | len | iters → password (both crypto paths)")
code('''my dog ate 7 blue socks       | gmail        | 1 | 20 | 200000 -> )h38Fc9(1mtd0S%{j#20
my dog ate 7 blue socks       | gmail        | 2 | 20 | 200000 -> %51u[JVETQ.;}wIlB}_E
correct horse battery staple  | GitHub       | 1 | 16 | 200000 -> ([a1A^olq6HHA!=N
correct horse battery staple  | '  github  ' | 1 | 16 | 200000 -> ([a1A^olq6HHA!=N   (== row above: trim+lower)
short                         | x            | 1 |  8 |  50000 -> b6}*=pUK
emoji test 🔐 ünïcode          | bank.example | 3 | 32 | 120000 -> C=PJ;p4yo6aSVI&5h7kMo7rlu]?xJ@SG''')
data("the exact salt bytes for row 1")
code('''site "gmail", rev 1  ->  salt string:  pwgen|v1|gmail|rev1
                         UTF-8 bytes (hex): 70 77 67 65 6e 7c 76 31 7c 67 6d 61 69 6c 7c 72 65 76 31
PBKDF2-HMAC-SHA256(phrase, salt, 200000) -> 28 bytes (20 for chars + 8 to force classes)''')

h(2, "6.6 Master verifier + at-rest AES-GCM (crypto.js:181-244)")
src("hashMaster / verifyMaster / deriveAesKey / encryptJSON / decryptJSON")
code('''async function hashMaster(master, saltBytes, iterations) {
  return await pbkdf2(master, saltBytes, iterations, 32);          // 32-byte verifier
}
async function verifyMaster(master, saltBytes, iterations, expectedBytes) {
  const cand = await hashMaster(master, saltBytes, iterations);
  if (cand.length !== expectedBytes.length) return false;
  let diff = 0;
  for (let i=0;i<cand.length;i++) diff |= cand[i] ^ expectedBytes[i];          // no early-out
  return diff === 0;                                                           // constant-time-ish
}
async function deriveAesKey(master, encSaltBytes, iterations) {
  const subtle = globalThis.crypto && globalThis.crypto.subtle;
  if (!subtle) throw new Error("...needs https or localhost...");
  const raw = await pbkdf2(master, encSaltBytes, iterations, 32);             // DIFFERENT salt than verifier
  return await subtle.importKey("raw", raw, { name:"AES-GCM" }, false, ["encrypt","decrypt"]);
}
async function encryptJSON(aesKey, obj) {
  const iv = globalThis.crypto.getRandomValues(new Uint8Array(12));           // fresh IV each write
  const data = enc.encode(JSON.stringify(obj));
  const ct = new Uint8Array(await crypto.subtle.encrypt({ name:"AES-GCM", iv }, aesKey, data));
  return b64(iv) + ":" + b64(ct);                                             // "iv:ciphertext"
}
async function decryptJSON(aesKey, blob) {
  const [ivPart, ctPart] = blob.split(":");
  const pt = await crypto.subtle.decrypt({ name:"AES-GCM", iv:unb64(ivPart) }, aesKey, unb64(ctPart));
  return JSON.parse(new TextDecoder().decode(pt));
}''')
notes([
    "verifier salt (`master_salt`) ≠ vault-key salt (`enc_salt`) ⇒ the stored verifier can never derive the vault key.",
    "AES-GCM is authenticated: wrong key or tampering throws on decrypt. Random 12-byte IV per write.",
    "`b64/unb64/bytesToHex/hexToBytes/randomBytes` (L181-244) are the byte/encoding helpers + the CSPRNG.",
])

# ===========================================================================
pagebreak()
h(1, "7. store.js — the data layer (the whole file) + the localStorage JSON")
h(2, "7.1 Keys + in-memory state (store.js:20-29)")
code('''const META_KEY = "pm_meta";
const VAULT_KEY = "pm_vault";
const DEFAULT_ITERATIONS = 200000;

let _aesKey = null;   // CryptoKey — vault key, memory only
let _entries = null;  // decrypted array, memory only
let _master = null;   // master password, memory ONLY while unlocked (to encrypt exports)
let _nextId = 1;''')

h(2, "7.2 create / unlock / lock (store.js:51-100)")
src("createMaster (store.js:51-72)")
code('''async function createMaster(master, exportPassword, iterations = DEFAULT_ITERATIONS) {
  const masterSalt = PMCrypto.randomBytes(16);
  const encSalt    = PMCrypto.randomBytes(16);
  const exportSalt = PMCrypto.randomBytes(16);
  const verifier       = await PMCrypto.hashMaster(master, masterSalt, iterations);
  const exportVerifier = await PMCrypto.hashMaster(exportPassword, exportSalt, iterations);
  const meta = {
    master_salt:     PMCrypto.bytesToHex(masterSalt),
    master_verifier: PMCrypto.bytesToHex(verifier),
    enc_salt:        PMCrypto.bytesToHex(encSalt),
    export_salt:     PMCrypto.bytesToHex(exportSalt),
    export_verifier: PMCrypto.bytesToHex(exportVerifier),
    iterations,
  };
  localStorage.setItem(META_KEY, JSON.stringify(meta));
  _aesKey = await PMCrypto.deriveAesKey(master, encSalt, iterations);
  _entries = []; _master = master; _nextId = 1;
  await _persist();                                   // write empty encrypted vault
}''')
src("unlock + lock (store.js:75-100)")
code('''async function unlock(master) {
  const meta = _loadMeta(); if (!meta) return false;
  const ok = await PMCrypto.verifyMaster(master,
    PMCrypto.hexToBytes(meta.master_salt), meta.iterations, PMCrypto.hexToBytes(meta.master_verifier));
  if (!ok) return false;                              // wrong master → UI shows error
  _aesKey = await PMCrypto.deriveAesKey(master, PMCrypto.hexToBytes(meta.enc_salt), meta.iterations);
  const blob = localStorage.getItem(VAULT_KEY);
  _entries = blob ? await PMCrypto.decryptJSON(_aesKey, blob) : [];
  _master = master;
  _nextId = _entries.reduce((m,e)=>Math.max(m,e.id),0) + 1;
  return true;
}
function lock() { _aesKey = null; _entries = null; _master = null; }''')

h(2, "7.3 Export-password functions (store.js:105-132)")
code('''function hasExportPassword() {                        // has it ever been set?
  const m = _loadMeta(); return !!(m && m.export_verifier);
}
async function verifyExportPassword(pw) {
  const m = _loadMeta(); if (!m || !m.export_verifier) return false;
  return PMCrypto.verifyMaster(pw, PMCrypto.hexToBytes(m.export_salt), m.iterations,
                               PMCrypto.hexToBytes(m.export_verifier));
}
async function setExportPassword(pw) {               // MIGRATION: add to a pre-existing vault
  const m = _loadMeta(); if (!m) throw new Error("No vault yet.");
  const exportSalt = PMCrypto.randomBytes(16);
  m.export_salt = PMCrypto.bytesToHex(exportSalt);
  m.export_verifier = PMCrypto.bytesToHex(await PMCrypto.hashMaster(pw, exportSalt, m.iterations));
  localStorage.setItem(META_KEY, JSON.stringify(m));  // patch meta in place; vault untouched
}
function getMaster() {                                // for encrypting exports only
  if (_master === null) throw new Error("Vault is locked.");
  return _master;
}''')
notes([
    "Migration path: old vault → `hasExportPassword()` false → UI prompts → `setExportPassword` patches "
    "`pm_meta`, leaving master + encrypted vault as-is.",
])

h(2, "7.4 persist + reads (store.js:134-166)")
code('''async function _persist() {                           // the ONLY writer of pm_vault
  if (!_aesKey || !_entries) throw new Error("Vault is locked.");
  localStorage.setItem(VAULT_KEY, await PMCrypto.encryptJSON(_aesKey, _entries));
}
function listEntries() {                              // sorted COPY
  if (!_entries) return [];
  return _entries.slice().sort((a,b)=>{
    if (!!b.needs_update - !!a.needs_update) return (b.needs_update?1:0)-(a.needs_update?1:0);
    return (b.updated_at||"").localeCompare(a.updated_at||"");   // needs_update first, then newest
  });
}
function getEntry(id){ return (_entries||[]).find(e=>e.id===id)||null; }
function exists(site, username){
  const s=site.trim().toLowerCase(), u=(username||"").trim().toLowerCase();
  return (_entries||[]).some(e => e.site_label.trim().toLowerCase()===s
                                && (e.username||"").trim().toLowerCase()===u);
}''')

h(2, "7.5 writes (store.js:169-218)")
code('''async function insertEntry({ site_label, username, password, revision, length, where_used }) {
  if (exists(site_label, username)) throw new Error("...already exists — use Rotate instead.");
  const entry = {
    id: _nextId++, site_label: site_label.trim(), username: (username||"").trim(),
    password, revision, length, where_used: (where_used||"").trim(),
    needs_update: false, updated_at: _now(),
  };
  _entries.push(entry); await _persist(); return entry;
}
async function updateEntryPassword(id, password, revision) {     // ROTATE
  const e = getEntry(id); if (!e) throw new Error("Entry not found.");
  e.password = password; e.revision = revision; e.needs_update = true; e.updated_at = _now();
  await _persist(); return e;                                    // needs_update=true → yellow
}
async function setWhereUsed(id, text){ const e=getEntry(id); if(!e) return;
  e.where_used=(text||"").trim(); await _persist(); }
async function setNeedsUpdate(id, value){ const e=getEntry(id); if(!e) return;
  e.needs_update=!!value; if(!value) e.updated_at=_now(); await _persist(); }   // clear yellow
async function deleteEntry(id){ _entries=_entries.filter(e=>e.id!==id); await _persist(); }''')
notes([
    "Every mutator ends in `_persist()` — re-encrypt the whole array, one localStorage write.",
    "`_now()` (L140-145) → `\"YYYY-MM-DD HH:MM\"`.",
])

h(2, "7.6 sync scaffolding (store.js:222-261)")
code('''function exportSnapshot(){ return { version:1, exported_at:_now(),
  iterations:getIterations(), entries:(_entries||[]).map(e=>({...e})) }; }   // PLAINTEXT (future PC sync)
async function mergeSnapshot(snapshot, { preferIncoming=false } = {}) {
  // merge by (site_label,username); newest updated_at wins; phone-first on ties
}
function wipeEverything(){ localStorage.removeItem(META_KEY); localStorage.removeItem(VAULT_KEY); lock(); }''')
p("Note: `exportSnapshot` is the **plaintext** sync snapshot, unrelated to the "
  "encrypted Excel export in `export.js`. It is wired to nothing yet.")

h(2, "7.7 REAL DATA — exactly what sits in localStorage")
data("localStorage['pm_meta'] — JSON, all hex; values illustrative (random per vault)")
code('''{
  "master_salt":     "9f3c1a77b2e4d058c61a0f9b4e7d2233",
  "master_verifier": "4b8e0c2d6f1a9e73c5b2a8d14f0e6b97a1c3d5e7f9012345678abcdef0123456",
  "enc_salt":        "1d2e3f405162738495a6b7c8d9e0f102",
  "export_salt":     "aa11bb22cc33dd44ee55ff6677889900",
  "export_verifier": "0fedcba987654321101112131415161718191a1b1c1d1e1f2021222324252627",
  "iterations":      200000
}
# salts = 16 bytes (32 hex). verifiers = 32 bytes (64 hex) = PBKDF2(pw, salt, iters, 32).
# This blob is NOT secret: it cannot decrypt pm_vault and cannot reveal any password.''')
data("localStorage['pm_vault'] — one AES-GCM blob: b64(iv) ':' b64(ciphertext)")
code('''"q1Wd3K8mZ0vY7tL4:Gx2b...«base64 of the AES-GCM ciphertext of the whole entries array»...=="
#  ^ 12-byte IV (16 b64 chars)  ^ ciphertext+128-bit GCM tag, base64''')
data("one decrypted entry object (the gmail row from the vectors above)")
code('''{
  "id": 1,
  "site_label": "gmail",
  "username": "me@gmail.com",
  "password": ")h38Fc9(1mtd0S%{j#20",     // present in MEMORY only (inside pm_vault when at rest)
  "revision": 1,
  "length": 20,
  "where_used": "Gmail primary + recovery",
  "needs_update": false,
  "updated_at": "2026-06-30 04:21"
}''')

# ===========================================================================
pagebreak()
h(1, "8. export.js — encrypted .xlsx (the whole pipeline + real format data)")
p("Builds a genuine Office password-protected workbook in pure JS. Two layers: a plain "
  "`.xlsx` (ZIP of OOXML), then ECMA-376 'agile encryption' inside an OLE2/CFB "
  "container. Stateless: `(masterPassword, rows) → encrypted bytes`.")

h(2, "8.1 Byte helpers (export.js:28-53)")
code('''function concatBytes(...arrs){ /* join Uint8Arrays */ }
function u16le(n){...}  function u32le(n){...}  function u64le(n){ /* lo32, hi32 little-endian */ }
function utf16le(str){ const b=new Uint8Array(str.length*2); const dv=new DataView(b.buffer);
  for (let i=0;i<str.length;i++) dv.setUint16(i*2, str.charCodeAt(i), true); return b; }   // password→UTF16LE
function b64(bytes){ let s=""; for (const x of bytes) s+=String.fromCharCode(x); return btoa(s); }
function xmlEsc(s){ return String(s==null?"":s).replace(/[&<>"']/g, c =>
  ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&apos;"}[c])); }''')

h(2, "8.2 Synchronous SHA-512 (export.js:55-162) — why & shape")
p("The agile KDF spins SHA-512 100,000×. Async `crypto.subtle.digest` = 100k awaited "
  "microtasks (~17 s). So SHA-512 is hand-written synchronously with 32-bit hi/lo word "
  "pairs (`KH`/`KL` = the 80 standard constants; reused `W_H`/`W_L` schedule). Verified "
  "vs Node native on 500+ inputs.")
src("the compression core (export.js:121-143, condensed)")
code('''const W_H = new Uint32Array(80), W_L = new Uint32Array(80);   // reused scratch (no per-call alloc)
function sha512(msg){
  // 8 × 64-bit state as hi/lo pairs (H0H,H0L ... H7H,H7L)
  // pad to 112 mod 128, append 0x80, then 128-bit big-endian bit length
  for (let off=0; off<total; off+=128){                       // per 1024-bit block
    for (let t=0;t<16;t++){ W_H[t]=dv.getUint32(off+t*8,false); W_L[t]=dv.getUint32(off+t*8+4,false); }
    for (let t=16;t<80;t++){ /* σ0,σ1 over hi/lo with carry into hi */ }
    // 80 rounds; each does 64-bit add as: lo += ...; hi += ... + floor(lo/2^32)
    let t1lo = (hL>>>0)+(S1L>>>0)+(chL>>>0)+(KL[t]>>>0)+(W_L[t]>>>0);
    let t1hi = ((hH>>>0)+(S1H>>>0)+(chH>>>0)+(KH[t]>>>0)+(W_H[t]>>>0)+Math.floor(t1lo/0x100000000))>>>0;
    // ...S0,maj,t2...; rotate a..h; fold into H with the same lo-then-hi carry
  }
  // emit 64 bytes big-endian (H0H,H0L,...,H7H,H7L)
}''')
notes([
    "Every 64-bit add is split: add the low 32 bits, carry `floor(lo/2^32)` into the high 32 bits.",
    "`>>> 0` forces unsigned 32-bit; `false` in DataView = big-endian (SHA is big-endian).",
])

h(2, "8.3 Web Crypto wrappers + the no-pad trick (export.js:165-177)")
code('''function rand(n){ return globalThis.crypto.getRandomValues(new Uint8Array(n)); }
async function hmacSha512(keyBytes, msg){
  const k = await subtleOf().importKey("raw", keyBytes, { name:"HMAC", hash:"SHA-512" }, false, ["sign"]);
  return new Uint8Array(await subtleOf().sign("HMAC", k, msg));
}
async function aesCbcNoPad(keyBytes, iv, data){     // data length MUST be a multiple of 16
  const key = await subtleOf().importKey("raw", keyBytes, { name:"AES-CBC" }, false, ["encrypt"]);
  const full = new Uint8Array(await subtleOf().encrypt({ name:"AES-CBC", iv }, key, data));
  return full.slice(0, data.length);               // drop the PKCS#7 block Web Crypto always appends
}''')
notes([
    "Office wants raw CBC; Web Crypto always PKCS#7-pads. Feed 16-multiple data, then slice back — "
    "CBC block i depends only on plaintext 1..i, so the prefix is the unpadded ciphertext.",
])

h(2, "8.4 CRC-32 + STORED ZIP writer (export.js:182-231)")
code('''function crc32(buf){ /* standard 0xEDB88320 table, init 0xFFFFFFFF, final XOR */ }
function zipStore(files){
  // per file: local header (sig 0x04034b50, method 0=STORED, crc, size×2, name) + raw data
  // then central directory (sig 0x02014b50 per file) + EOCD (sig 0x06054b50)
}''')
data("ZIP local file header fields written per part (export.js:204-209)")
table(
    ["Offset", "Bytes", "Value"],
    [
        ["0", "4", "0x04034b50 (local file header signature)"],
        ["4", "2", "20 (version needed)"],
        ["6", "2", "0 (flags)"],
        ["8", "2", "0 (method = STORED / no compression)"],
        ["10", "2", "0 (mod time)"],
        ["12", "2", "0x21 (mod date = 1980-01-01)"],
        ["14", "4", "crc32(data)"],
        ["18 / 22", "4 / 4", "compressed size = uncompressed size = data.length"],
        ["26 / 28", "2 / 2", "name length / extra length (0)"],
    ],
)

h(2, "8.5 buildXlsx — the spreadsheet (export.js:241-302)")
src("rows → cells (export.js:241-253)")
code('''function buildXlsx(rows){
  const headers = ["Site","Username / Email","Length","Note","Password"];
  let body = `<row r="1">${headers.map((h,i)=>textCell(colLetter(i)+"1",h)).join("")}</row>`;
  rows.forEach((r,ri)=>{
    const R = ri+2;
    body += `<row r="${R}">`
      + textCell(colLetter(0)+R, r.site)
      + textCell(colLetter(1)+R, r.email)
      + numCell (colLetter(2)+R, r.length)
      + textCell(colLetter(3)+R, r.where)
      + textCell(colLetter(4)+R, r.password)
      + `</row>`;
  });
  // ...wrap in <worksheet><sheetData>, then zipStore the 6 parts...
}
const textCell = (ref,v) => `<c r="${ref}" t="inlineStr"><is><t xml:space="preserve">${xmlEsc(v)}</t></is></c>`;
const numCell  = (ref,v) => `<c r="${ref}"><v>${Number(v)||0}</v></c>`;''')
notes([
    "5 columns: Site · Username/Email · Length · Note · Password. The PHRASE is never a column.",
    "Text uses `t=\"inlineStr\"` (no shared-strings table); Length is numeric. `xml:space=preserve` keeps exact text.",
])
data("the six OOXML parts zipStore writes (export.js:294-301)")
code('''[Content_Types].xml
_rels/.rels
xl/workbook.xml
xl/_rels/workbook.xml.rels
xl/styles.xml
xl/worksheets/sheet1.xml''')
data("xl/worksheets/sheet1.xml — actual output for ONE entry (gmail, len 20)")
code('''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>
<row r="1">
  <c r="A1" t="inlineStr"><is><t xml:space="preserve">Site</t></is></c>
  <c r="B1" t="inlineStr"><is><t xml:space="preserve">Username / Email</t></is></c>
  <c r="C1" t="inlineStr"><is><t xml:space="preserve">Length</t></is></c>
  <c r="D1" t="inlineStr"><is><t xml:space="preserve">Note</t></is></c>
  <c r="E1" t="inlineStr"><is><t xml:space="preserve">Password</t></is></c>
</row>
<row r="2">
  <c r="A2" t="inlineStr"><is><t xml:space="preserve">gmail</t></is></c>
  <c r="B2" t="inlineStr"><is><t xml:space="preserve">me@gmail.com</t></is></c>
  <c r="C2"><v>20</v></c>
  <c r="D2" t="inlineStr"><is><t xml:space="preserve">Gmail primary + recovery</t></is></c>
  <c r="E2" t="inlineStr"><is><t xml:space="preserve">)h38Fc9(1mtd0S%{j#20</t></is></c>
</row>
</sheetData></worksheet>''')
data("xl/workbook.xml + xl/styles.xml (verbatim, fixed)")
code('''<workbook xmlns="...spreadsheetml/2006/main" xmlns:r="...officeDocument/2006/relationships">
  <sheets><sheet name="Vault" sheetId="1" r:id="rId1"/></sheets>
</workbook>

<styleSheet xmlns="...spreadsheetml/2006/main">
  <fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts>
  <fills count="1"><fill><patternFill patternType="none"/></fill></fills>
  <borders count="1"><border/></borders>
  <cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
  <cellXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/></cellXfs>
  <cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>   <!-- silences openpyxl warning -->
</styleSheet>''')

h(2, "8.6 encryptAgile — the encryption (export.js:315-379)")
src("the password KDF + block-key derivation (export.js:315-331)")
code('''const SPIN_COUNT = 100000, SEGMENT = 4096;
async function encryptAgile(pkg, password){
  const keyDataSalt = rand(16);   // for package + integrity IVs
  const keySalt     = rand(16);   // for the password key-encryptor

  let h = sha512(concatBytes(keySalt, utf16le(password)));      // H0 = SHA512(keySalt ‖ UTF16LE(pw))
  for (let i=0;i<SPIN_COUNT;i++) h = sha512(concatBytes(u32le(i), h));   // spin 100000×
  const baseHash = h;
  const deriveKey = (blockKey) => sha512(concatBytes(baseHash, new Uint8Array(blockKey))).slice(0,32);

  const secretKey = rand(32);     // the REAL key that encrypts the package
  const verifier  = rand(16);
  const encVerifierInput = await aesCbcNoPad(deriveKey(BK_VERIFIER_INPUT), keySalt, verifier);
  const encVerifierValue = await aesCbcNoPad(deriveKey(BK_VERIFIER_VALUE), keySalt, sha512(verifier));
  const encKeyValue      = await aesCbcNoPad(deriveKey(BK_KEY_VALUE),      keySalt, secretKey);''')
src("package segments + integrity HMAC (export.js:333-352)")
code('''  const segs = [];
  for (let off=0,i=0; off<pkg.length; off+=SEGMENT,i++){
    let chunk = pkg.slice(off, off+SEGMENT);
    if (chunk.length % 16) { const pad=new Uint8Array(Math.ceil(chunk.length/16)*16); pad.set(chunk); chunk=pad; }
    const iv = sha512(concatBytes(keyDataSalt, u32le(i))).slice(0,16);     // per-segment IV
    segs.push(await aesCbcNoPad(secretKey, iv, chunk));
  }
  const encryptedPackage = concatBytes(u64le(pkg.length), ...segs);       // u64 length + segments

  const hmacKey = rand(64);
  const ivKey   = sha512(concatBytes(keyDataSalt, new Uint8Array(BK_HMAC_KEY))).slice(0,16);
  const encHmacKey   = await aesCbcNoPad(secretKey, ivKey, hmacKey);
  const hmacValue    = await hmacSha512(hmacKey, encryptedPackage);
  const ivVal        = sha512(concatBytes(keyDataSalt, new Uint8Array(BK_HMAC_VALUE))).slice(0,16);
  const encHmacValue = await aesCbcNoPad(secretKey, ivVal, hmacValue);''')
data("the five fixed block keys (export.js:307-311)")
code('''BK_VERIFIER_INPUT = [fe a7 d2 76 3b 4b 9e 79]
BK_VERIFIER_VALUE = [d7 aa 0f 6d 30 61 34 4e]
BK_KEY_VALUE      = [14 6e 0b e7 ab ac d0 d6]
BK_HMAC_KEY       = [5f b2 ad 01 0c b9 e1 f6]
BK_HMAC_VALUE     = [a0 67 7f 02 b2 2c 84 33]   # each derives a distinct sub-key from baseHash''')
data("EncryptionInfo: the 8-byte prefix + XML (export.js:354-376)")
code('''prefix bytes: 04 00 04 00 40 00 00 00      # versionMajor=4, versionMinor=4, flags=0x40 (fAgile)

<encryption xmlns="...office/2006/encryption" xmlns:p="...keyEncryptor/password">
  <keyData saltSize="16" blockSize="16" keyBits="256" hashSize="64"
           cipherAlgorithm="AES" cipherChaining="ChainingModeCBC" hashAlgorithm="SHA512"
           saltValue="b64(keyDataSalt)"/>
  <dataIntegrity encryptedHmacKey="b64(encHmacKey)" encryptedHmacValue="b64(encHmacValue)"/>
  <keyEncryptors><keyEncryptor uri="...keyEncryptor/password">
    <p:encryptedKey spinCount="100000" saltSize="16" blockSize="16" keyBits="256" hashSize="64"
       cipherAlgorithm="AES" cipherChaining="ChainingModeCBC" hashAlgorithm="SHA512"
       saltValue="b64(keySalt)"
       encryptedVerifierHashInput="b64(encVerifierInput)"
       encryptedVerifierHashValue="b64(encVerifierValue)"
       encryptedKeyValue="b64(encKeyValue)"/>
  </keyEncryptor></keyEncryptors>
</encryption>

# returns { encryptionInfo, encryptedPackage } — the two CFB streams.''')
notes([
    "The password protects `secretKey`; `secretKey` encrypts the package (segmented CBC, per-segment IV).",
    "`EncryptedPackage` = u64le(plaintextLen) ‖ segments. `dataIntegrity` is an HMAC-SHA512 over that stream.",
    "NOTHING here is the password itself — only salts, the spin count and encrypted verifier/key/HMAC.",
])

h(2, "8.7 buildCFB — the OLE2 container (export.js:384-515)")
p("Wraps the two streams in a Compound File Binary (v3, 512-byte sectors) — a tiny FAT "
  "filesystem-in-a-file that Excel expects.")
notes([
    "Small streams (`EncryptionInfo` < 4096) go in the **mini stream + mini-FAT**; big streams "
    "(`EncryptedPackage`) get full 512-byte FAT sectors.",
    "Directory entries are a balanced BST (`build(lo,hi)`, L467-473); CFB name order = shorter name "
    "first, else case-insensitive UTF-16 (`cmp`, L462-463).",
    "Layout in file order: 512-byte header → directory → mini-FAT → mini container → big streams → FAT.",
])
data("CFB header fields (export.js:494-509)")
table(
    ["Offset", "Value", "Meaning"],
    [
        ["0", "D0 CF 11 E0 A1 B1 1A E1", "CFB magic"],
        ["24 / 26", "0x003E / 0x0003", "minor / major version (v3)"],
        ["28", "0xFFFE", "little-endian byte order"],
        ["30 / 32", "0x0009 / 0x0006", "sector shift 2^9=512 / mini shift 2^6=64"],
        ["44", "nFat", "number of FAT sectors"],
        ["48", "firstDir", "first directory sector"],
        ["56", "0x1000", "mini-stream cutoff = 4096"],
        ["60 / 64", "firstMiniFat / miniFatCount", "mini-FAT start / count"],
        ["76…", "FAT sector ids", "the DIFAT (first 109 entries)"],
    ],
)

h(2, "8.8 Public pipeline (export.js:520-541)")
code('''async function buildEncryptedXlsx(masterPassword, rows){
  if (!subtleOf()) throw new Error("Encrypted export needs a secure context (https or localhost).");
  const pkg = buildXlsx(rows);                                              // 1. plain .xlsx
  const { encryptionInfo, encryptedPackage } = await encryptAgile(pkg, masterPassword);  // 2. encrypt
  return buildCFB([ { name:"EncryptionInfo", data:encryptionInfo },
                    { name:"EncryptedPackage", data:encryptedPackage } ]);  // 3. wrap → final bytes
}
function entriesToRows(entries){
  return (entries||[]).map(e => ({ site:e.site_label||"", email:e.username||"",
    length:e.length||0, where:e.where_used||"", password:e.password||"" }));   // NO phrase, NO revision
}''')
p("Verified with `msoffcrypto-tool` + `openpyxl`: the master password decrypts to a "
  "valid sheet with the exact columns/values; any other password is rejected.")

# ===========================================================================
pagebreak()
h(1, "9. app.js — the controller (the whole file) + the rendered HTML")
h(2, "9.1 helpers + routing (app.js:10-42)")
code('''const $  = (sel) => document.querySelector(sel);
const $$ = (sel) => Array.from(document.querySelectorAll(sel));
const SCREENS = ["screen-setup","screen-unlock","screen-app","screen-manual"];
let _returnScreen = "screen-app";
function show(screenId){ SCREENS.forEach(id => $("#"+id).hidden = (id!==screenId)); window.scrollTo(0,0); }
function route(){
  if (!PMStore.isInitialised()) return show("screen-setup");
  if (!PMStore.isUnlocked())    return show("screen-unlock");
  show("screen-app"); loadVault();
}
let toastTimer=null;
function toast(msg){ const t=$("#toast"); t.textContent=msg; t.hidden=false;
  clearTimeout(toastTimer); toastTimer=setTimeout(()=>(t.hidden=true),2200); }
function escapeHtml(s){ return (s||"").replace(/[&<>"']/g, c =>
  ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c])); }''')

h(2, "9.2 setup step 1 + unlock (app.js:45-75)")
code('''let _pendingMaster = null;   // bridges step 1 → step 2 only
$("#setup-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const master=$("#setup-master").value, confirm=$("#setup-confirm").value;
  if (master.length < 6)   { /* error */ return; }
  if (master !== confirm)  { /* error */ return; }
  if (!PMCrypto.hasSubtle()){ /* needs secure context */ return; }
  _pendingMaster = master; openExportSetup("create");          // → step 2 (modal)
});
$("#unlock-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const ok = await PMStore.unlock($("#unlock-master").value);
  if (!ok) { $("#unlock-error").textContent="Incorrect master password."; return; }
  $("#unlock-master").value=""; route();
});''')

h(2, "9.3 nav + generator (app.js:78-133)")
code('''$("#nav-lock").addEventListener("click",   e=>{ e.preventDefault(); PMStore.lock(); route(); });
$("#nav-manual").addEventListener("click", e=>{ e.preventDefault(); _returnScreen="screen-app"; renderManual(); show("screen-manual"); });
$("#show-phrase").addEventListener("change", e=>{ phraseEl.type = e.target.checked ? "text":"password"; });
lengthEl.addEventListener("input", ()=> lenVal.textContent = lengthEl.value);
function clampLen(v){ return Math.max(8, Math.min(parseInt(v,10)||20, 64)); }

$("#btn-preview").addEventListener("click", async ()=>{
  const phrase=phraseEl.value.trim(), site=siteEl.value.trim();
  if (!phrase||!site){ setGenMsg("Phrase and site are required."); return; }
  const pw = await PMCrypto.derivePassword(phrase, site, 1, clampLen(lengthEl.value), PMStore.getIterations());
  $("#preview-box").hidden=false; $("#preview-pass").textContent = pw;     // shown, NOT saved
});
$("#btn-save").addEventListener("click", async ()=>{
  const phrase=phraseEl.value.trim(), site=siteEl.value.trim();
  if (!phrase||!site){ setGenMsg("..."); return; }
  const length=clampLen(lengthEl.value);
  const password = await PMCrypto.derivePassword(phrase, site, 1, length, PMStore.getIterations());
  await PMStore.insertEntry({ site_label:site, username:usernameEl.value, password,
                              revision:1, length, where_used:whereEl.value });
  phraseEl.value=""; siteEl.value=""; usernameEl.value=""; whereEl.value="";   // CLEAR phrase
  loadVault(); toast("Password generated & saved");
});''')
notes([
    "Always derives at revision 1 for new entries. Phrase is cleared from the DOM right after save.",
])

h(2, "9.4 render + wire the vault (app.js:143-248)")
src("renderVault — the card template (app.js:160-184)")
code('''list.innerHTML = filtered.map((e)=>{
  const masked = "•".repeat(Math.min(e.password.length, 24));
  return `
  <div class="entry ${e.needs_update ? "flagged" : ""}" data-id="${e.id}">
    <div class="entry-top">
      <div>
        <span class="entry-site">${escapeHtml(e.site_label)}</span>
        ${e.username ? `<span class="entry-user"> · ${escapeHtml(e.username)}</span>` : ""}
        <span class="rev-badge">rev ${e.revision}</span>
      </div>
      <span class="entry-meta">${e.length} chars · ${escapeHtml(e.updated_at)}</span>
    </div>
    <div class="pass-row">
      <div class="pass-val" data-pass="${escapeHtml(e.password)}" data-shown="0">${masked}</div>
      <button class="icon-btn copy">Copy</button>
    </div>
    <div class="notes-label">Where used ${e.needs_update ? "· needs updating on the real site" : ""}</div>
    <textarea class="notes-box" rows="2">${escapeHtml(e.where_used)}</textarea>
    <div class="entry-actions">
      <button class="mini-btn rotate">↻ Rotate</button>
      ${e.needs_update ? `<button class="mini-btn confirm">✓ Mark updated</button>` : ""}
      <button class="mini-btn del">Delete</button>
    </div>
  </div>`;
}).join("");''')
src("wireEntries — per-card listeners (app.js:189-248, condensed)")
code('''passEl.addEventListener("click", ()=>{                       // reveal / hide
  const shown = passEl.dataset.shown==="1";
  passEl.textContent = shown ? "•".repeat(Math.min(passEl.dataset.pass.length,24)) : passEl.dataset.pass;
  passEl.dataset.shown = shown ? "0" : "1";
});
card.querySelector(".copy").addEventListener("click", async ()=>{
  try { await navigator.clipboard.writeText(passEl.dataset.pass); toast("Password copied"); }
  catch { toast("Copy failed — reveal and copy manually"); }
});
notes.addEventListener("blur", async ()=>{ if (notes.value===original) return;
  await PMStore.setWhereUsed(id, notes.value); toast("Notes saved"); });      // save on blur
card.querySelector(".rotate").addEventListener("click", ()=> openRotate(id));
confirmBtn?.addEventListener("click", async ()=>{ await PMStore.setNeedsUpdate(id,false); loadVault(); });
card.querySelector(".del").addEventListener("click", async ()=>{
  if (!confirm("Delete this entry? You can still re-derive it from your phrase later.")) return;
  await PMStore.deleteEntry(id); loadVault(); });''')
notes([
    "`data-pass` carries the real (HTML-escaped) password so reveal/copy read it without re-deriving.",
    "Notes save only on blur and only if changed. Delete asks first (re-derivable, so it's reassuring).",
])

h(2, "9.5 rotate (app.js:253-280)")
code('''function openRotate(id){ rotateId=id; const ent=PMStore.getEntry(id);
  $("#rotate-target").textContent = `${ent.site_label}${ent.username?" · "+ent.username:""} (currently rev ${ent.revision})`;
  $("#rotate-modal").hidden=false; $("#rotate-phrase").focus(); }
$("#rotate-go").addEventListener("click", async ()=>{
  const phrase=$("#rotate-phrase").value.trim();
  const ent=PMStore.getEntry(rotateId), newRev=ent.revision+1;
  const password = await PMCrypto.derivePassword(phrase, ent.site_label, newRev, ent.length, PMStore.getIterations());
  await PMStore.updateEntryPassword(rotateId, password, newRev);             // flags yellow
  closeRotate(); toast(`Rotated to rev ${newRev} — now update it on the real site`); loadVault();
});''')

h(2, "9.6 export: setup / verify / build (app.js:282-394)")
src("the two-job setup modal (app.js:285-335, condensed)")
code('''function openExportSetup(mode){                               // "create" (first run) | "set" (migration)
  _exportSetupMode = mode;
  if (mode==="create"){ /* title "Create your export password"; button "Create vault →"; cancel "Back" */ }
  else               { /* title "Set your export password";    button "Save & export →"; cancel "Cancel" */ }
  $("#export-setup-modal").hidden=false; $("#export-setup-pass").focus();
}
$("#export-setup-go").addEventListener("click", async ()=>{
  const pw=$("#export-setup-pass").value, confirm=$("#export-setup-confirm").value;
  if (pw.length<6){ /* error */ return; }  if (pw!==confirm){ /* error */ return; }
  if (_exportSetupMode==="create"){
    await PMStore.createMaster(_pendingMaster, pw); _pendingMaster=null; closeExportSetup(); toast("Vault created"); route();
  } else {
    await PMStore.setExportPassword(pw); closeExportSetup(); doExport();      // migration → export now
  }
});''')
src("the export gate + verify (app.js:338-365)")
code('''$("#nav-export").addEventListener("click", (e)=>{
  e.preventDefault();
  if (!PMStore.isUnlocked())                       { route(); return; }            // guard 1
  if ((PMStore.listEntries()||[]).length===0)      { toast("Vault is empty — nothing to export"); return; }  // guard 2
  if (!PMCrypto.hasSubtle())                        { toast("Export needs a secure context (https or localhost)"); return; }  // guard 3
  if (!PMStore.hasExportPassword())                { openExportSetup("set"); return; }   // guard 4 → migration
  openExportVerify();
});
$("#export-verify-go").addEventListener("click", async ()=>{
  const pw=$("#export-verify-pass").value;
  if (!pw){ /* error */ return; }
  if (!(await PMStore.verifyExportPassword(pw))){ $("#export-verify-msg").textContent="Incorrect export password."; return; }
  closeExportVerify(); doExport();
});''')
src("doExport + filename (app.js:367-394)")
code('''function exportFilename(){ const d=new Date(), p=n=>String(n).padStart(2,"0");
  return `vault-export-${d.getFullYear()}-${p(d.getMonth()+1)}-${p(d.getDate())}.xlsx`; }   // vault-export-2026-06-30.xlsx
async function doExport(){
  if (!PMCrypto.hasSubtle()){ toast("Export needs a secure context (https or localhost)"); return; }
  toast("Encrypting your backup… this can take a few seconds");
  await new Promise(r => setTimeout(r, 60));                                  // let the toast PAINT before the sync KDF
  const rows  = PMExport.entriesToRows(PMStore.listEntries());
  const bytes = await PMExport.buildEncryptedXlsx(PMStore.getMaster(), rows); // master encrypts the FILE
  const blob  = new Blob([bytes], { type:"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" });
  const url   = URL.createObjectURL(blob);
  const a = document.createElement("a"); a.href=url; a.download=exportFilename();
  document.body.appendChild(a); a.click(); document.body.removeChild(a);
  setTimeout(()=>URL.revokeObjectURL(url), 4000);
  toast("Exported — open it with your master password");
}''')
notes([
    "Four ordered guards on `#nav-export`; guard 4 is the no-export-password migration branch.",
    "`setTimeout(60)` lets the toast render before the synchronous SHA-512 spin freezes the thread.",
    "`getMaster()` is the only place the master password reaches the file; it is never written anywhere.",
])

h(2, "9.7 boot (app.js:396-407)")
code('''function renderManual(){ $("#manual-body").innerHTML = MANUAL_HTML; }
if ("serviceWorker" in navigator) {
  window.addEventListener("load", ()=> navigator.serviceWorker.register("sw.js").catch(()=>{}));
}
route();                                                                      // paint the first screen''')

# ===========================================================================
h(1, "10. manual.js — structure + wiring")
p("One global `MANUAL_HTML` (`manual.js:7-126`): the manual as a single HTML string "
  "(TOC + 11 sections). Rendered by `renderManual()`. The only logic is the bottom "
  "back-link:")
code('''document.addEventListener("click", (e)=>{
  if (e.target && e.target.id === "manual-back-bottom") {
    e.preventDefault();
    const target = (typeof _returnScreen !== "undefined") ? _returnScreen : "screen-app";
    document.querySelectorAll("section[id^='screen-']").forEach(s => s.hidden = (s.id !== target));
    window.scrollTo(0,0);
  }
});''')
p("Section ids inside the manual: m-idea, m-two-secrets, m-generate, m-rotate, "
  "m-determinism, m-offline, m-sync, m-security, m-edge, m-backup, m-recover.")

# ===========================================================================
pagebreak()
h(1, "11. End-to-end call chains (exact functions + lines)")
h(2, "11.1 First run → vault created")
code('''route() L22  ─ !isInitialised ─►  show("screen-setup")
#setup-form submit L46  ─►  validate  ─►  _pendingMaster=master ; openExportSetup("create") L60
#export-setup-go L315 (mode create)  ─►  PMStore.createMaster(_pendingMaster, pw) L324
  store.createMaster L51  ─►  3 salts ; hashMaster×2 ; setItem(pm_meta) ; deriveAesKey ; _master=master ; _persist()
route() L328  ─►  show("screen-app") + loadVault()''')
h(2, "11.2 Generate & save")
code('''#btn-save L114  ─►  PMCrypto.derivePassword(phrase, site, 1, length, iters) L121  (crypto L150)
  ─►  PMStore.insertEntry({...}) L122  (store L169: exists? → push → _persist[AES-GCM] )
  ─►  clear inputs (incl. phrase) L129  ─►  loadVault() L130''')
h(2, "11.3 Unlock")
code('''route() L23  ─►  show("screen-unlock")
#unlock-form L64  ─►  PMStore.unlock(master) L65  (store L75: verifyMaster → deriveAesKey → decryptJSON → _master)
  ─ ok ─►  route()  ─►  screen-app''')
h(2, "11.4 Rotate → mark updated")
code('''.rotate click L226  ─►  openRotate(id) L254
#rotate-go L267  ─►  derivePassword(phrase, site, rev+1, len, iters)  ─►  updateEntryPassword L275 (needs_update=true → yellow)
.confirm click L230  ─►  setNeedsUpdate(id,false) L232  ─►  white''')
h(2, "11.5 Export")
code('''#nav-export L338  ─►  guards (unlocked / non-empty / subtle / hasExportPassword)
#export-verify-go L356  ─►  verifyExportPassword(pw) L361  ─ ok ─►  doExport() L364
doExport L373  ─►  entriesToRows(listEntries) L379  ─►  buildEncryptedXlsx(getMaster(), rows) L380
  export L520  ─►  buildXlsx → encryptAgile(pkg, master) → buildCFB  ─►  bytes
  ─►  <a download="vault-export-YYYY-MM-DD.xlsx"> click L387''')
h(2, "11.6 Lock")
code('''#nav-lock L78  ─►  PMStore.lock() (store L96: _aesKey=_entries=_master=null)  ─►  route()  ─►  screen-unlock''')

# ===========================================================================
h(1, "12. Consolidated data reference")
h(2, "12.1 Schemas")
table(
    ["Artifact", "Shape"],
    [
        ["pm_meta", "{ master_salt, master_verifier, enc_salt, export_salt, export_verifier, iterations }"],
        ["pm_vault", "string  `b64(iv12) ':' b64(ciphertext+gcmTag)`"],
        ["entry", "{ id, site_label, username, password, revision, length, where_used, needs_update, updated_at }"],
        ["export row", "{ site, email, length, where, password }   (from entriesToRows — no phrase, no revision)"],
        ["snapshot", "{ version, exported_at, iterations, entries[] }   (plaintext; future sync)"],
    ],
)
h(2, "12.2 Constants that must never drift")
table(
    ["Constant", "Value", "Where"],
    [
        ["DEFAULT_ITERATIONS", "200000", "store.js:22"],
        ["salt grammar", "`pwgen|v1|<site>|rev<n>`", "crypto.js:153"],
        ["FULL length", "85", "crypto.js:23 (26+26+10+23)"],
        ["SPIN_COUNT", "100000", "export.js:312"],
        ["SEGMENT", "4096", "export.js:313"],
        ["CACHE_VERSION", "vault-v3", "sw.js:7"],
        ["AES-GCM IV", "12 random bytes / write", "crypto.js:227"],
        ["CFB cutoff", "4096 (mini-stream)", "export.js:385/504"],
    ],
)
h(2, "12.3 The crypto at a glance")
table(
    ["Purpose", "Primitive", "Key from"],
    [
        ["Generate password", "PBKDF2-HMAC-SHA256, 200k", "phrase + salt(site,rev)"],
        ["Master / export verifier", "PBKDF2-HMAC-SHA256, 200k → 32B", "password + its salt"],
        ["Vault at rest", "AES-256-GCM", "PBKDF2(master, enc_salt)"],
        ["Excel file", "AES-256-CBC + HMAC-SHA512 (agile)", "SHA512-spun(master, keySalt)"],
    ],
)

# ===========================================================================
pagebreak()
h(1, "Appendix — function index (every function → file:line)")
h(2, "crypto.js")
table(["Function","Line"],[
    ["sha256","45"],["concat","87"],["hmacSha256","94"],["pbkdf2Pure","112"],["pbkdf2","133"],
    ["derivePassword","150"],["bytesToHex/hexToBytes/b64/unb64","181-199"],
    ["hashMaster","201"],["verifyMaster","205"],["deriveAesKey","218"],
    ["encryptJSON","225"],["decryptJSON","233"],["randomBytes","242"],["hasSubtle","251"],
])
h(2, "store.js")
table(["Function","Line"],[
    ["isInitialised/isUnlocked","31/34"],["_loadMeta/getIterations","38/43"],
    ["createMaster","51"],["unlock","75"],["lock","96"],
    ["hasExportPassword","105"],["verifyExportPassword","109"],["setExportPassword","120"],["getMaster","129"],
    ["_persist/_now","134/140"],["listEntries/getEntry/exists","148/156/159"],
    ["insertEntry","169"],["updateEntryPassword","189"],["setWhereUsed","200"],["setNeedsUpdate","207"],["deleteEntry","215"],
    ["exportSnapshot","222"],["mergeSnapshot","233"],["wipeEverything","257"],
])
h(2, "export.js")
table(["Function","Line"],[
    ["concatBytes/u16le/u32le/u64le","28-43"],["utf16le/b64/xmlEsc","44-53"],
    ["sha512","85"],["rand","165"],["hmacSha512","166"],["aesCbcNoPad","173"],
    ["crc32","182"],["zipStore","197"],["colLetter","233"],["textCell/numCell","238/239"],["buildXlsx","241"],
    ["encryptAgile","315"],["buildCFB","384"],["buildEncryptedXlsx","520"],["entriesToRows","533"],
])
h(2, "app.js")
table(["Handler / function","Line"],[
    ["$/$$/show/route","10/11/16/21"],["toast/escapeHtml","30/38"],
    ["#setup-form","46"],["#unlock-form","64"],["nav handlers","78-82"],
    ["btn-preview/btn-save","102/114"],["loadVault/renderVault/wireEntries","138/143/189"],["#search","250"],
    ["openRotate/#rotate-go","254/267"],
    ["openExportSetup/#export-setup-go","285/315"],
    ["#nav-export/openExportVerify/#export-verify-go","338/347/356"],
    ["exportFilename/doExport","367/373"],["renderManual/boot","397/402"],
])

spacer()
p("End of blueprint. Generated 2026-06-30.", style="Standard")

# ===========================================================================
#  ODT ASSEMBLY  (identical machinery to build_docs.py)
# ===========================================================================
body_xml = "\n".join(parts)

NS = (
    'xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
    'xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0" '
    'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" '
    'xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0" '
    'xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0" '
    'xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0"'
)

content_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<office:document-content {NS} office:version="1.2">
<office:automatic-styles/>
<office:body><office:text>
{body_xml}
</office:text></office:body>
</office:document-content>'''

styles_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<office:document-styles {NS} office:version="1.2">
<office:font-face-decls>
  <style:font-face style:name="Sans" svg:font-family="'Liberation Sans'" style:font-family-generic="swiss"/>
  <style:font-face style:name="Mono" svg:font-family="'DejaVu Sans Mono'" style:font-family-generic="modern" style:font-pitch="fixed"/>
</office:font-face-decls>
<office:styles>
  <style:default-style style:family="paragraph">
    <style:paragraph-properties fo:line-height="120%"/>
    <style:text-properties style:font-name="Sans" fo:font-size="11pt"/>
  </style:default-style>

  <style:style style:name="Standard" style:family="paragraph">
    <style:paragraph-properties fo:margin-top="0cm" fo:margin-bottom="0.18cm" fo:line-height="120%"/>
    <style:text-properties style:font-name="Sans" fo:font-size="11pt" fo:color="#222222"/>
  </style:style>

  <style:style style:name="DocTitle" style:family="paragraph">
    <style:paragraph-properties fo:text-align="center" fo:margin-bottom="0.1cm"/>
    <style:text-properties style:font-name="Sans" fo:font-size="24pt" fo:font-weight="bold" fo:color="#0b5cab"/>
  </style:style>
  <style:style style:name="DocSubtitle" style:family="paragraph">
    <style:paragraph-properties fo:text-align="center" fo:margin-bottom="0.6cm"/>
    <style:text-properties style:font-name="Sans" fo:font-size="12pt" fo:font-style="italic" fo:color="#666666"/>
  </style:style>

  <style:style style:name="Heading_20_1" style:display-name="Heading 1" style:family="paragraph" style:default-outline-level="1">
    <style:paragraph-properties fo:margin-top="0.55cm" fo:margin-bottom="0.2cm" fo:keep-with-next="always"/>
    <style:text-properties style:font-name="Sans" fo:font-size="18pt" fo:font-weight="bold" fo:color="#0f6fd6"/>
  </style:style>
  <style:style style:name="Heading_20_2" style:display-name="Heading 2" style:family="paragraph" style:default-outline-level="2">
    <style:paragraph-properties fo:margin-top="0.4cm" fo:margin-bottom="0.15cm" fo:keep-with-next="always"/>
    <style:text-properties style:font-name="Sans" fo:font-size="14pt" fo:font-weight="bold" fo:color="#11457f"/>
  </style:style>
  <style:style style:name="Heading_20_3" style:display-name="Heading 3" style:family="paragraph" style:default-outline-level="3">
    <style:paragraph-properties fo:margin-top="0.3cm" fo:margin-bottom="0.1cm" fo:keep-with-next="always"/>
    <style:text-properties style:font-name="Sans" fo:font-size="12pt" fo:font-weight="bold" fo:color="#222222"/>
  </style:style>

  <style:style style:name="Code" style:family="paragraph">
    <style:paragraph-properties fo:background-color="#f2f4f7" fo:padding="0.12cm" fo:margin-top="0.1cm" fo:margin-bottom="0.1cm" fo:border="0.5pt solid #d7dde5"/>
    <style:text-properties style:font-name="Mono" fo:font-size="9pt" fo:color="#1a2733"/>
  </style:style>

  <style:style style:name="ListItem" style:family="paragraph" style:parent-style-name="Standard">
    <style:paragraph-properties fo:margin-bottom="0.08cm"/>
  </style:style>

  <style:style style:name="PageBreak" style:family="paragraph" style:parent-style-name="Standard">
    <style:paragraph-properties fo:break-before="page"/>
  </style:style>

  <style:style style:name="TblHead" style:family="paragraph">
    <style:paragraph-properties fo:margin="0cm"/>
    <style:text-properties style:font-name="Sans" fo:font-size="10pt" fo:font-weight="bold" fo:color="#ffffff"/>
  </style:style>
  <style:style style:name="TblCell" style:family="paragraph">
    <style:paragraph-properties fo:margin="0cm"/>
    <style:text-properties style:font-name="Sans" fo:font-size="10pt" fo:color="#222222"/>
  </style:style>

  <style:style style:name="Bold" style:family="text">
    <style:text-properties fo:font-weight="bold"/>
  </style:style>
  <style:style style:name="Mono" style:family="text">
    <style:text-properties style:font-name="Mono" fo:font-size="9pt" fo:background-color="#f2f4f7" fo:color="#0b3d66"/>
  </style:style>

  <text:list-style style:name="Bullets">
    <text:list-level-style-bullet text:level="1" text:bullet-char="•">
      <style:list-level-properties text:space-before="0.5cm" text:min-label-width="0.4cm"/>
    </text:list-level-style-bullet>
  </text:list-style>
  <text:list-style style:name="Numbers">
    <text:list-level-style-number text:level="1" style:num-format="1" style:num-suffix=".">
      <style:list-level-properties text:space-before="0.5cm" text:min-label-width="0.5cm"/>
    </text:list-level-style-number>
  </text:list-style>

  <style:style style:name="Tbl" style:family="table">
    <style:table-properties style:width="17cm" table:align="margins" fo:margin-top="0.15cm" fo:margin-bottom="0.25cm"/>
  </style:style>
  <style:style style:name="Tbl.col" style:family="table-column">
    <style:table-column-properties style:use-optimal-column-width="true"/>
  </style:style>
  <style:style style:name="Tbl.hcell" style:family="table-cell">
    <style:table-cell-properties fo:background-color="#0f6fd6" fo:padding="0.12cm" fo:border="0.5pt solid #9bb6d4"/>
  </style:style>
  <style:style style:name="Tbl.cell" style:family="table-cell">
    <style:table-cell-properties fo:background-color="#ffffff" fo:padding="0.12cm" fo:border="0.5pt solid #cdd6e2"/>
  </style:style>
</office:styles>
<office:automatic-styles>
  <style:page-layout style:name="PL">
    <style:page-layout-properties fo:page-width="21cm" fo:page-height="29.7cm" style:print-orientation="portrait" fo:margin-top="2cm" fo:margin-bottom="2cm" fo:margin-left="1.6cm" fo:margin-right="1.6cm"/>
  </style:page-layout>
</office:automatic-styles>
<office:master-styles>
  <style:master-page style:name="Standard" style:page-layout-name="PL"/>
</office:master-styles>
</office:document-styles>'''

meta_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<office:document-meta xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:meta="urn:oasis:names:tc:opendocument:xmlns:meta:1.0" office:version="1.2">
<office:meta>
  <dc:title>Vault Mobile - Code Blueprint (annotated source)</dc:title>
  <dc:creator>pass-manager-mobile</dc:creator>
  <dc:date>2026-06-30T00:00:00</dc:date>
  <meta:generator>build_blueprint.py</meta:generator>
</office:meta>
</office:document-meta>'''

manifest_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0" manifest:version="1.2">
  <manifest:file-entry manifest:full-path="/" manifest:media-type="application/vnd.oasis.opendocument.text"/>
  <manifest:file-entry manifest:full-path="content.xml" manifest:media-type="text/xml"/>
  <manifest:file-entry manifest:full-path="styles.xml" manifest:media-type="text/xml"/>
  <manifest:file-entry manifest:full-path="meta.xml" manifest:media-type="text/xml"/>
</manifest:manifest>'''

# Validate the XML parts parse before zipping.
import xml.dom.minidom as _md
for name, blob in (("content.xml", content_xml), ("styles.xml", styles_xml),
                   ("meta.xml", meta_xml), ("manifest.xml", manifest_xml)):
    _md.parseString(blob)

out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Vault_Mobile_Blueprint.odt")
with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as z:
    # mimetype MUST be first and stored uncompressed.
    zi = zipfile.ZipInfo("mimetype")
    zi.compress_type = zipfile.ZIP_STORED
    z.writestr(zi, "application/vnd.oasis.opendocument.text")
    z.writestr("META-INF/manifest.xml", manifest_xml)
    z.writestr("content.xml", content_xml)
    z.writestr("styles.xml", styles_xml)
    z.writestr("meta.xml", meta_xml)

print("Wrote", out_path)
print("Body blocks:", len(parts))
