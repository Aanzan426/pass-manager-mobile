#!/usr/bin/env python3
"""
build_docs.py — generates Vault_Mobile_Documentation.odt (OpenDocument Text) with
no external dependencies. An .odt is just a ZIP of XML parts, so we build it by
hand. Open the result in LibreOffice Writer.

This is the MOBILE-ONLY documentation for the pass-manager-mobile project (the
offline PWA). The desktop app is referenced only where it matters (cross-platform
parity and the optional sync). For the combined desktop+mobile reference, see the
parent project's docs/Vault_Documentation.odt.
"""
import html
import re
import zipfile
import os

parts = []  # accumulates the document body XML

# ---------------------------------------------------------------------------
# Inline / block helpers
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

# ===========================================================================
#  DOCUMENT CONTENT  (mobile-only)
# ===========================================================================
title("Vault Mobile — Offline Password Generator (PWA)")
subtitle("pass-manager-mobile · complete project documentation · v1.1 · 2026-06-15")

p("This document is the single, complete reference for Vault Mobile — the phone "
  "application in the `pass-manager-mobile` repository. It is a fully offline "
  "Progressive Web App (PWA) that generates strong passwords on the phone, with no "
  "server and no internet connection required once installed. It covers what the app "
  "is, how it works, how it was built and tested, how to deploy and install it, and "
  "what is planned next — down to the algorithm, the test vectors and the verified "
  "results.")
p("Live app: `https://aanzan426.github.io/pass-manager-mobile/`. The companion "
  "desktop app lives in the parent project; this document only touches it where it "
  "matters (cross-platform parity in section 9 and the optional sync in section 15).")

# ---- Contents ----
h(1, "Contents")
numbers([
    "Overview (what this is, in one minute)",
    "The core concept — deterministic passwords",
    "How the app is built (the PWA, one engine)",
    "The generation algorithm, step by step",
    "Security model",
    "The app's files & structure",
    "Offline & self-contained",
    "Data model (encrypted phone storage)",
    "Determinism & parity with the desktop",
    "Testing — what, how, and the results",
    "Deployment (GitHub Pages, public/private, install)",
    "Usage guide",
    "Backup — encrypted Excel export (the failsafe)",
    "Edge cases & gotchas",
    "Roadmap & future plans (incl. Sync to PC)",
    "Glossary",
    "Appendix A — reference test vectors",
    "Appendix B — useful commands",
])

# ---- 1. Overview ----
pagebreak()
h(1, "1. Overview (what this is, in one minute)")
p("Vault Mobile is a password manager built on an unusual but powerful idea: instead "
  "of storing the passwords you log in with, it re-creates them on demand from a "
  "phrase you keep in your head. You memorise one phrase. The app turns "
  "`phrase + site + revision` into a strong password containing upper-case, "
  "lower-case, digits and symbols. The same inputs always produce the same password, "
  "so the result never has to be stored or memorised — only the phrase does.")
p("What makes the mobile version special:")
bullets([
    "**Fully offline.** It is a static PWA (plain HTML/CSS/JS) — no server, no build "
    "step, no internet required to run once installed.",
    "**Runs entirely on the phone.** Generation happens in the phone's browser; data "
    "is stored encrypted in the phone's own storage.",
    "**Installable.** Add it to the home screen and it launches full-screen like a "
    "native app, working with no network at all.",
    "**Private by construction.** It makes zero external network calls — even the "
    "fonts are bundled — so nothing about your usage leaves the phone.",
])
p("It also produces **byte-for-byte identical passwords** to the desktop app for the "
  "same inputs — proven by test (see section 10) — so the phone and PC always agree.")

# ---- 2. Core concept ----
h(1, "2. The core concept — deterministic passwords")
p("A normal password manager is a vault: it stores secrets and you retrieve them. "
  "Vault is a generator: it computes secrets and you reproduce them. The difference "
  "matters because a computed password does not need to exist anywhere until the "
  "moment you need it.")
p("The recipe has three ingredients:")
bullets([
    "**Phrase** — the secret you memorise. Never stored, never transmitted.",
    "**Site label** — e.g. `gmail`. Makes every site's password different.",
    "**Revision** — a counter you bump to rotate a password without changing your phrase.",
])
p("Because the output depends only on these three things (plus a chosen length), the "
  "same phrase + site + revision always yields the same password — on any device, "
  "forever. That is the whole point, and it is why a single typo in the phrase "
  "produces a completely different password: determinism cuts both ways.")

# ---- 3. How the app is built ----
h(1, "3. How the app is built (the PWA, one engine)")
bullets([
    "A **static PWA**: plain HTML/CSS/JavaScript. No build step, no server, no backend.",
    "Generation runs in the phone via the browser's **Web Crypto** (`crypto.subtle`) "
    "for native PBKDF2/AES, with a **pure-JavaScript PBKDF2 fallback** so it still "
    "works even without a secure context.",
    "Data is stored in the phone's **localStorage**, encrypted at rest with **AES-GCM** "
    "(the key is derived from the master password).",
    "A **service worker** caches the whole app so it runs fully offline after first load.",
    "Fonts are **bundled locally** — the app makes zero external network calls.",
])
p("The generation engine (`js/crypto.js`) is an exact port of the desktop's "
  "`core/crypto.py`: the identical procedure described next. That is what guarantees "
  "the phone and PC produce the same passwords.")

# ---- 4. Algorithm ----
h(1, "4. The generation algorithm, step by step")
p("Function: `derivePassword(phrase, site, revision, length, iterations)`. It is pure "
  "and deterministic — no randomness is ever introduced.")
numbers([
    "Clamp `length` to a minimum of 8.",
    "Normalise the site: `site.trim().toLowerCase()` so `Gmail`, `gmail` and "
    "` gmail ` match.",
    "Build the salt string: `pwgen|v1|<normalised-site>|rev<revision>` (UTF-8 bytes).",
    "Derive `length + 8` bytes via PBKDF2-HMAC-SHA256 with the configured iteration "
    "count (200,000 by default).",
    "Fill every output position by mapping each derived byte onto the full character "
    "set (`byte % charset.length`).",
    "Build a deterministic permutation of positions using a seeded Fisher-Yates "
    "shuffle, driven by the derived bytes (`k = dk[(i*7) % dklen] % (i+1)`).",
    "Force one character from each class (upper, lower, digit, symbol) into the first "
    "four permuted positions using the 8 extra bytes — guaranteeing all four classes "
    "are present in varied positions.",
    "Join and return the characters.",
])
h(2, "4.1 Character set")
table(
    ["Class", "Characters"],
    [
        ["Upper", "A-Z"],
        ["Lower", "a-z"],
        ["Digit", "0-9"],
        ["Special", "!@#$%^&*()-_=+[]{};:,.?"],
    ],
)
p("Quotes, backslash, spaces and backtick are deliberately excluded because they "
  "frequently break when pasted into shells, CSVs, or sites with naive validation.")
h(2, "4.2 Parameters")
table(
    ["Parameter", "Value", "Notes"],
    [
        ["Hash", "PBKDF2-HMAC-SHA256", "Standard; native via Web Crypto, pure-JS fallback"],
        ["Iterations", "200,000 (default)", "Stored in the vault meta; safe to change later"],
        ["Default length", "20", "User-selectable 8–64 per entry"],
        ["Salt", "pwgen|v1|<site>|rev<n>", "Encodes site + revision; keeps output reproducible"],
    ],
)

# ---- 5. Security model ----
h(1, "5. Security model")
bullets([
    "**The phrase is never stored** and never leaves the phone. You type it when you "
    "generate or rotate.",
    "**The master password is never stored** — only a one-way PBKDF2 verifier is kept, "
    "used to check it on unlock (constant-time-style comparison).",
    "**Saved passwords are encrypted at rest** with **AES-GCM**. The encryption key is "
    "derived from the master password using a separate salt from the verifier, so the "
    "verifier can never be used to derive the key.",
    "**Two independent secrets.** The master password only locks the app and encrypts "
    "storage; it does NOT affect generated passwords. Generated passwords depend solely "
    "on phrase + site + revision + length — which is why the phone and PC agree.",
    "**Locking or closing forgets the key** from memory, re-locking the vault.",
    "**The export password** (set at vault creation) is also kept only as a one-way "
    "verifier. It gates the encrypted Excel export; the exported file is encrypted with "
    "the master password, and neither password is ever written into the file (section 13).",
    "**No network surface.** The app never talks to a server, so there is no endpoint "
    "to attack and nothing to intercept in transit.",
])
p("Consequence to understand: forgetting the master password means the stored list "
  "cannot be decrypted — but any individual password can still be re-derived from the "
  "phrase. The stored data is a convenience, not the source of the passwords "
  "themselves.")

# ---- 6. Files & structure ----
pagebreak()
h(1, "6. The app's files & structure")
h(2, "6.1 File layout")
code(
"""pass-manager-mobile/
├── index.html             ← the whole app (one page, all screens)
├── manifest.webmanifest   ← PWA metadata (name, icons, standalone)
├── sw.js                  ← service worker → offline caching
├── css/
│   ├── fonts.css          ← @font-face for the bundled fonts
│   └── style.css          ← mobile-first "Bugatti" theme
├── fonts/
│   ├── inter.woff2            ← UI font (variable, Latin subset)
│   └── jetbrains-mono.woff2   ← monospace font (variable, Latin subset)
├── js/
│   ├── crypto.js          ← derivation + encryption (port of core/crypto.py)
│   ├── store.js           ← encrypted localStorage data layer
│   ├── manual.js          ← in-app manual content
│   └── app.js             ← UI controller
├── icons/                 ← app icons (192 / 512 / maskable-512)
├── docs/                  ← this documentation (+ build_docs.py)
├── README.md
├── LICENSE
└── .gitignore"""
)
h(2, "6.2 What each JavaScript file does")
table(
    ["File", "Responsibility"],
    [
        ["crypto.js", "SHA-256/HMAC/PBKDF2 (native + pure-JS), derivePassword, master "
                      "hash/verify, AES-GCM encrypt/decrypt. Exact port of the Python engine."],
        ["store.js", "Encrypted vault in localStorage: create/unlock/lock, list, insert, "
                     "rotate, notes, mark-updated, delete; plus exportSnapshot/mergeSnapshot "
                     "for future PC sync."],
        ["app.js", "UI controller: screen routing, generation, vault rendering, rotate modal, "
                   "lock, service-worker registration."],
        ["manual.js", "The in-app manual content (rendered into the Manual screen)."],
    ],
)
h(2, "6.3 The screens")
bullets([
    "**Setup** — first run: create the master password (shown only when no vault exists).",
    "**Unlock** — enter the master password to decrypt and open the vault.",
    "**App** — the generator (phrase, site, username, length, notes) plus the searchable "
    "vault list.",
    "**Manual** — the built-in, offline how-to (from `manual.js`).",
])

# ---- 7. Offline & self-contained ----
h(1, "7. Offline & self-contained")
h(2, "7.1 The service worker")
p("`sw.js` (cache name `vault-v2`) pre-caches every asset on install, then serves "
  "them cache-first, so after the very first load the app runs with no network at "
  "all. Whenever any cached file changes, the `CACHE_VERSION` constant is bumped so "
  "the phone fetches the new version and drops the old cache.")
code(
"""const CACHE_VERSION = "vault-v2";
const ASSETS = [
  ".", "index.html", "manifest.webmanifest",
  "css/fonts.css", "css/style.css",
  "fonts/inter.woff2", "fonts/jetbrains-mono.woff2",
  "js/crypto.js", "js/store.js", "js/manual.js", "js/app.js",
  "icons/icon-192.png", "icons/icon-512.png", "icons/icon-maskable-512.png",
];"""
)
h(2, "7.2 Bundled fonts (zero external calls)")
p("The app's fonts — Inter (UI) and JetBrains Mono (monospace) — are included in the "
  "repo under `fonts/` and loaded from `css/fonts.css`. Both are **variable** fonts: "
  "a single woff2 per family covers every weight (Inter `100 900`, JetBrains Mono "
  "`100 800`), which is why one file per family is enough. There is **no Google Fonts "
  "request** — the app makes zero external network calls, so it is pixel-perfect "
  "offline and nothing about your usage leaves the phone.")

# ---- 8. Data model ----
h(1, "8. Data model (encrypted phone storage)")
p("The vault lives in the phone's `localStorage` under two keys:")
table(
    ["Key", "Contents"],
    [
        ["pm_meta", "JSON: master salt, master verifier, encryption salt, iterations "
                    "(all hex strings). Not secret on its own — it cannot decrypt anything."],
        ["pm_vault", "The entries, encrypted as a single AES-GCM blob "
                     "(format `b64(iv):b64(ciphertext)`)."],
    ],
)
p("While unlocked, the AES key and the decrypted entries are held only in memory; "
  "locking or closing the app forgets them. Each entry has the same shape the desktop "
  "uses, so the two can sync later:")
table(
    ["Field", "Meaning"],
    [
        ["id", "Unique identifier"],
        ["site_label", "The site/service label (lower-cased for matching)"],
        ["username", "Optional username/email at that site"],
        ["password", "The derived password (only present in memory while unlocked)"],
        ["revision", "Rotation counter"],
        ["length", "Password length for this entry"],
        ["where_used", "Free-text notes: where the password is used"],
        ["needs_update", "True after a rotation, until confirmed on the real site"],
        ["updated_at", "Last change timestamp"],
    ],
)
p("The list is sorted so entries that `need update` (just rotated) float to the top, "
  "then by most-recently-updated.")

# ---- 9. Parity ----
h(1, "9. Determinism & parity with the desktop")
p("The mobile generator is a faithful JavaScript port of the desktop's Python one. "
  "Every step — salt construction, byte derivation, the Fisher-Yates permutation, the "
  "forced-class placement — matches exactly. This is not assumed; it is verified by "
  "running the JS against reference values produced by the Python implementation (see "
  "section 10.1 and Appendix A). Both the native Web Crypto path and the pure-"
  "JavaScript fallback path were checked, and both reproduce the Python output "
  "exactly. The practical upshot: a password generated on the phone is the same string "
  "you would get on the PC, so you can use either device interchangeably.")

# ---- 10. Testing ----
pagebreak()
h(1, "10. Testing — what, how, and the results")
p("Testing fell into four areas: determinism parity, end-to-end behaviour in a real "
  "browser, live-deployment verification, and the font self-hosting check.")

h(2, "10.1 Determinism parity test")
p("**What:** confirm the phone produces identical passwords to the PC. **How:** "
  "generate reference passwords from the Python engine for six varied inputs, then run "
  "the same inputs through the JavaScript engine — once using native `crypto.subtle`, "
  "once with `crypto.subtle` disabled to force the pure-JS PBKDF2. **Result:** all six "
  "match on both paths.")
table(
    ["Phrase / Site / Rev / Len / Iter", "Expected password", "JS match"],
    [
        ["my dog ate 7 blue socks / gmail / 1 / 20 / 200000", ")h38Fc9(1mtd0S%{j#20", "✓ (both)"],
        ["my dog ate 7 blue socks / gmail / 2 / 20 / 200000", "%51u[JVETQ.;}wIlB}_E", "✓ (both)"],
        ["correct horse battery staple / GitHub / 1 / 16 / 200000", "([a1A^olq6HHA!=N", "✓ (both)"],
        ["correct horse battery staple / '  github  ' / 1 / 16 / 200000", "([a1A^olq6HHA!=N", "✓ (both)"],
        ["short / x / 1 / 8 / 50000", "b6}*=pUK", "✓ (both)"],
        ["emoji test 🔐 ünïcode / bank.example / 3 / 32 / 120000", "C=PJ;p4yo6aSVI&5h7kMo7rlu]?xJ@SG", "✓ (both)"],
    ],
)
p("Note rows 3 and 4: `GitHub` and `'  github  '` produce the SAME password, proving "
  "the trim + lower-case normalisation works.")

h(2, "10.2 End-to-end browser tests")
p("**What:** every user-facing flow. **How:** the app was served over `localhost` (a "
  "secure context) and driven in a real Chromium browser at a phone viewport "
  "(412×915). **Result:** all flows passed.")
table(
    ["Flow", "Result"],
    [
        ["Create master password → app opens", "Pass"],
        ["Preview password (gmail, len 20)", "Pass — showed )h38Fc9(1mtd0S%{j#20, matching PC"],
        ["Generate & Save → appears in vault (rev 1, masked)", "Pass"],
        ["Reveal / hide password, Copy button", "Pass"],
        ["Edit 'where used' notes (save on blur)", "Pass"],
        ["Rotate → rev 2, notes box turns yellow", "Pass"],
        ["Mark updated → box returns to white", "Pass"],
        ["Lock → reload → unlock", "Pass — entry persisted (AES-GCM round-trip), rev 2, white"],
        ["Manual screen renders", "Pass"],
    ],
)

h(2, "10.3 Live deployment verification (GitHub Pages)")
p("**What:** confirm the published site serves correctly and can host a working PWA. "
  "**How:** fetched every asset and inspected status + content type, then loaded the "
  "live HTTPS URL in a real browser. **Result:** all green.")
table(
    ["Check", "Result"],
    [
        ["All 15 files", "HTTP 200"],
        ["index.html content type", "text/html"],
        ["manifest.webmanifest content type", "application/manifest+json"],
        ["sw.js content type", "application/javascript (required, or SW is rejected)"],
        ["fonts content type", "font/woff2"],
        ["Secure context (window.isSecureContext)", "true"],
        ["Web Crypto (window.crypto.subtle)", "available"],
        ["Service worker", "active (offline cache primed)"],
        ["Console errors", "none (only harmless accessibility hints)"],
    ],
)

h(2, "10.4 Font self-hosting verification")
p("**What:** prove the app makes no external network calls. **How:** loaded the page "
  "and listed every network request. **Result:** every request was same-origin "
  "(localhost / github.io); zero requests to Google Fonts or any third party. The "
  "Inter and JetBrains Mono variable fonts load from the repo's `fonts/` folder.")

h(2, "10.5 Encrypted export verification")
p("**What:** confirm the password-protected `.xlsx` is a genuine Office-encrypted file "
  "that opens only with the master password. **How:** generated the file both in Node and "
  "in a real browser (driving the actual Export flow), then decrypted it with the "
  "independent `msoffcrypto-tool` and read it with `openpyxl`. The pure-JS SHA-512 was "
  "also checked against Node's native SHA-512 on 500+ random and boundary-length inputs. "
  "**Result:** the export password and any wrong password are rejected; the master "
  "password decrypts the file to a valid sheet with the exact columns and values "
  "(special characters and unicode preserved). The migration path — an existing vault "
  "with no export password — was also driven in the browser and verified.")

# ---- 11. Deployment ----
pagebreak()
h(1, "11. Deployment (GitHub Pages, public/private, install)")
h(2, "11.1 Pushing to a branch is NOT a running app")
p("Putting files on GitHub only stores the code; GitHub does not run `index.html` as "
  "a website. Raw file links will not work as the app (wrong content type, not a "
  "secure origin, the service worker will not register). Storage is not the same as a "
  "usable app.")
h(2, "11.2 What GitHub Pages is")
p("GitHub Pages is a free feature that serves the repo's static files as a real HTTPS "
  "site at `https://<user>.github.io/<repo>/`. That URL is a secure origin, so the "
  "browser crypto works, the PWA installs, and it then runs fully offline. Pages "
  "publishes from a branch/folder you select.")
p("To enable: repo → Settings → Pages → Source: Deploy from a branch → choose branch "
  "+ `/ (root)` → Save. After ~1 minute it shows 'Your site is live at …'. For this "
  "project that is `https://aanzan426.github.io/pass-manager-mobile/`.")
h(2, "11.3 Public vs private")
bullets([
    "On the free plan, Pages only serves from a **public** repo.",
    "You **can switch the repo back to private after installing** — the installed app "
    "keeps working because the service worker cached everything onto the phone.",
    "While private, the github.io URL goes dark. You only need it live again at "
    "install/update time: when you reinstall (new phone, cleared data) or want a code "
    "update. Flip it public for a few minutes, then private again.",
    "Safe to make public: only the code is exposed — no passwords, keys or vault data; "
    "the phrase never leaves the phone.",
])
h(2, "11.4 Installing on the phone (Chrome, Galaxy M21)")
numbers([
    "Open the Pages URL in Chrome.",
    "Land on 'Create your master password' and set it up on the phone.",
    "Chrome menu (⋮) → Add to Home screen / Install app.",
    "Launch from the icon — full-screen, offline-capable.",
    "Optionally switch the repo to private afterwards.",
])
p("Reminder: the vault on the phone is independent and per-device — entries live only "
  "in this phone's local storage.")
h(2, "11.5 Testing it from your PC first (optional)")
p("Before deploying you can serve it locally over `localhost`, which is also a secure "
  "context, and open it in a desktop browser or on the phone over the same Wi-Fi:")
code(
"""cd pass-manager-mobile
python3 -m http.server 8099
# then open http://localhost:8099
# (or http://<PC-LAN-IP>:8099 from the phone on the same Wi-Fi)"""
)
p("Note: some browsers restrict `crypto.subtle` to https; over a plain LAN IP the "
  "pure-JS fallback still generates passwords, but for full parity with the installed "
  "app use the Pages URL or `localhost`.")

# ---- 12. Usage guide ----
h(1, "12. Usage guide")
numbers([
    "Open the app and set (first run) or enter your master password.",
    "On first run, also set your export password when prompted (section 13).",
    "Type your phrase and a site label; optionally a username; pick a length.",
    "Preview to see the password, or Generate & Save to store it.",
    "In the vault, tap a password to reveal/hide; Copy to copy.",
    "Record where you used it in the notes box (saves automatically).",
    "To change a password: Rotate, re-enter your phrase — the revision bumps and the "
    "notes box turns yellow.",
    "Change it on the real website, then tap 'Mark updated' to clear the yellow.",
])
p("**Consistency matters:** always spell a site label the same way and keep its "
  "length fixed — both are part of the recipe. The vault remembers each entry's "
  "revision and length for you.")

# ---- 13. Backup ----
h(1, "13. Backup — encrypted Excel export (the failsafe)")
p("Losing the phone would otherwise mean losing access, so Vault can export the whole "
  "vault to a real, password-protected Excel file (`.xlsx`) — built entirely in the "
  "phone, offline, with no libraries.")
h(2, "13.1 The two-password flow")
numbers([
    "At vault creation you set a second 'export password' (a popup right after the master "
    "password). Only a one-way verifier is stored — never the password itself.",
    "Tap 'Export' in the top bar. You are asked for the export password first — this "
    "gates the action, so a grabbed but unlocked phone cannot silently dump the vault.",
    "The app builds the spreadsheet and encrypts the FILE with the master password.",
    "Opening the file in Excel / Google Sheets / LibreOffice prompts for the master "
    "password before any content is shown.",
])
h(2, "13.2 Columns")
p("Each entry becomes one row: **Site · Username/Email · Length · Note · Password**. The "
  "phrase is deliberately NOT exported — it is never stored anywhere, and writing it into "
  "a file would defeat the entire design.")
h(2, "13.3 How the encryption works (no libraries)")
bullets([
    "The `.xlsx` is assembled by hand: a ZIP (stored, with CRC-32) of the OOXML parts.",
    "It is then wrapped in Microsoft Office 'agile encryption' (ECMA-376): SHA-512 + "
    "AES-256-CBC + HMAC-SHA512, inside an OLE2 / Compound File Binary container.",
    "Web Crypto performs the AES and HMAC; a small pure-JS SHA-512 runs the 100,000-round "
    "key derivation quickly (the async digest would add 100k microtasks and take ~17s).",
    "The master password is used only as the file key — it is never stored, in the file "
    "or on the phone.",
])
p("Vaults created before this feature simply prompt to set an export password the first "
  "time you tap Export, then export immediately.")

# ---- 14. Edge cases ----
h(1, "14. Edge cases & gotchas")
table(
    ["Situation", "What happens"],
    [
        ["Same phrase + site + revision", "Identical password, every time, on any device"],
        ["Site typed with different case/spaces", "Trimmed + lower-cased, so it still matches"],
        ["gmail vs gmail.com", "Different label → different password. Be consistent"],
        ["Change the length", "Different password — length is part of the recipe"],
        ["Forget the revision", "It is saved in the vault and shown as 'rev n'"],
        ["Forget the master password", "Stored list cannot be decrypted, but passwords can be "
                                       "re-derived from the phrase"],
        ["One character off in the phrase", "Completely different passwords — by design"],
        ["Clear browser data / uninstall", "The phone-local vault is erased; re-derive from "
                                           "the phrase (or restore a future export)"],
        ["Open as a bare file:// page", "Generation still works (pure-JS PBKDF2), but vault "
                                        "encryption needs a secure context"],
        ["Forget the export password", "It only gates the export; you can set a new one and "
                                       "re-export. The file's own lock is the master password"],
        ["Lost the export .xlsx", "Harmless on its own — it still needs the master password to "
                                  "open. Just export a fresh one"],
    ],
)

# ---- 15. Roadmap ----
pagebreak()
h(1, "15. Roadmap & future plans")
h(2, "15.1 Done")
bullets([
    "Full offline PWA with the same interface and the same engine as the desktop app.",
    "Deterministic generation, rotation with the yellow/white workflow, encrypted "
    "phone-local storage, installable to the home screen.",
    "Verified determinism parity between phone and PC (both crypto paths).",
    "Self-hosted variable fonts (zero external calls).",
    "Encrypted Excel (.xlsx) export — a master-password-protected failsafe, gated by a "
    "second export password, built offline with no libraries (section 13).",
    "Live deployment on GitHub Pages, verified end to end.",
])
h(2, "15.2 Next: Sync to PC")
p("Goal: a 'Sync' button so the notes and revision numbers you change on the phone "
  "flow back to the desktop app's database, and vice-versa — without making the phone "
  "depend on the PC for daily use.")
p("**Design decisions:**")
bullets([
    "**Source of truth = the phone (phone-first).** The phone always works offline; "
    "the PC is a mirror the phone pushes to when reachable. Newest `updated_at` wins "
    "per `(site_label, username)`.",
    "**What syncs:** only metadata (site labels, usernames, revisions, notes, flags) — "
    "never the phrase. Passwords are re-derivable, so they need not travel.",
    "**Transport options:** (a) Tailscale — a private encrypted tunnel between just "
    "your phone and PC, works anywhere; (b) same home Wi-Fi — direct, no internet; "
    "(c) an encrypted export file moved manually (USB / shared folder) for a "
    "no-live-server option.",
    "**Already scaffolded:** `store.js` exposes `exportSnapshot()` and `mergeSnapshot()` "
    "with the merge rules above, ready to wire to a button and a small sync endpoint "
    "on the desktop.",
])
p("Important reality check, by design: 'data on the PC' and 'works when the PC is "
  "off' cannot both be true for the same copy of the data — you cannot read from a "
  "powered-down computer. Vault resolves this by making the phone self-sufficient (it "
  "re-derives everything) and treating the PC as an optional synced backup, not a "
  "dependency.")
h(2, "15.3 Possible later additions")
bullets([
    "A one-tap 'copy + open site' helper.",
    "Optional biometric unlock on the phone (WebAuthn) layered over the master password.",
    "Import/restore flow on the phone from an encrypted export.",
    "A small desktop endpoint to receive phone syncs automatically when both are online.",
])

# ---- 16. Glossary ----
h(1, "16. Glossary")
table(
    ["Term", "Meaning"],
    [
        ["Phrase", "The memorised secret used to generate passwords. Never stored."],
        ["Master password", "Locks the app and encrypts stored data. Separate from the phrase."],
        ["Export password", "Second password gating the Excel export. Stored only as a verifier."],
        ["Revision", "A counter bumped to rotate a password while keeping it reproducible."],
        ["PBKDF2", "A slow, salted key-derivation function; the core of the generator."],
        ["AES-GCM", "Authenticated encryption used to protect the stored vault on the phone."],
        ["Office agile encryption", "ECMA-376 scheme (SHA-512 + AES-CBC + HMAC in an OLE2 file) "
                                    "used to password-protect the exported .xlsx."],
        ["PWA", "Progressive Web App — a website installable like an app, works offline."],
        ["Service worker", "Background script that caches the app for offline use."],
        ["Secure context", "An origin (https or localhost) where browser crypto is allowed."],
        ["localStorage", "The phone browser's per-site key/value storage; holds the vault."],
        ["GitHub Pages", "Free static hosting that serves a repo as an HTTPS website."],
        ["Determinism", "Same inputs always give the same output — no randomness."],
    ],
)

# ---- 16. Appendix A ----
h(1, "Appendix A — reference test vectors")
p("These are the canonical (input → output) pairs used to verify parity. Format: "
  "phrase | site | revision | length | iterations → password.")
code(
"""my dog ate 7 blue socks | gmail        | 1 | 20 | 200000 -> )h38Fc9(1mtd0S%{j#20
my dog ate 7 blue socks | gmail        | 2 | 20 | 200000 -> %51u[JVETQ.;}wIlB}_E
correct horse battery staple | GitHub   | 1 | 16 | 200000 -> ([a1A^olq6HHA!=N
correct horse battery staple | '  github  ' | 1 | 16 | 200000 -> ([a1A^olq6HHA!=N
short | x                    | 1 |  8 |  50000 -> b6}*=pUK
emoji test (lock) ünïcode | bank.example | 3 | 32 | 120000 -> C=PJ;p4yo6aSVI&5h7kMo7rlu]?xJ@SG"""
)

# ---- 17. Appendix B ----
h(1, "Appendix B — useful commands")
code(
"""# Serve locally for testing (secure context = localhost)
cd pass-manager-mobile
python3 -m http.server 8099
# then open http://localhost:8099  (or http://<PC-LAN-IP>:8099 on the phone)

# Regenerate this documentation
python3 docs/build_docs.py

# After changing any cached file, bump CACHE_VERSION in sw.js so phones update."""
)

spacer()
p("End of document. Generated 2026-06-15.", style="Standard")

# ===========================================================================
#  ODT ASSEMBLY
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
    <style:text-properties style:font-name="Mono" fo:font-size="9.5pt" fo:color="#1a2733"/>
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
    <style:text-properties style:font-name="Mono" fo:font-size="9.5pt" fo:background-color="#f2f4f7" fo:color="#0b3d66"/>
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
    <style:page-layout-properties fo:page-width="21cm" fo:page-height="29.7cm" style:print-orientation="portrait" fo:margin-top="2cm" fo:margin-bottom="2cm" fo:margin-left="2cm" fo:margin-right="2cm"/>
  </style:page-layout>
</office:automatic-styles>
<office:master-styles>
  <style:master-page style:name="Standard" style:page-layout-name="PL"/>
</office:master-styles>
</office:document-styles>'''

meta_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<office:document-meta xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:meta="urn:oasis:names:tc:opendocument:xmlns:meta:1.0" office:version="1.2">
<office:meta>
  <dc:title>Vault Mobile - Offline Password Generator (PWA) - Documentation</dc:title>
  <dc:creator>pass-manager-mobile</dc:creator>
  <dc:date>2026-06-15T00:00:00</dc:date>
  <meta:generator>build_docs.py</meta:generator>
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

out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Vault_Mobile_Documentation.odt")
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
