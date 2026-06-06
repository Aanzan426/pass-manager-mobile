# Vault — Mobile (offline PWA)

A phone-friendly, **fully offline** version of the desktop password manager.
Same look, same engine — and it generates **byte-for-byte identical passwords**
to the desktop app (`core/crypto.py`), verified by test.

It is a static Progressive Web App: plain HTML/CSS/JS, **no server, no build, no
internet** required to run once installed. Your data lives encrypted in the
phone's own storage.

## How it works

- **Generation runs in the phone.** `phrase + site + revision → password` via
  PBKDF2-HMAC-SHA256 (200,000 iterations), mapped onto upper/lower/digits/symbols.
  No randomness, so it is reproducible and matches your PC exactly.
- **Master password** locks the app and encrypts the saved vault at rest
  (AES-GCM, key derived from the master password with its own salt).
- **The phrase is never stored** — you type it to generate or rotate.
- **Rotation** bumps a revision and flags the entry **yellow** until you confirm
  you changed it on the real site (then **white**).

## Files

```
pass_manager_mobile/
├── index.html             ← the whole app (one page, all screens)
├── manifest.webmanifest   ← PWA metadata (name, icons, standalone)
├── sw.js                  ← service worker → offline caching
├── css/style.css          ← mobile-first "Bugatti" theme
├── js/
│   ├── crypto.js          ← password derivation + encryption (port of core/crypto.py)
│   ├── store.js           ← encrypted localStorage data layer
│   ├── manual.js          ← in-app manual content
│   └── app.js             ← UI controller
└── icons/                 ← app icons (192/512 + maskable)
```

## Running it on your phone

A PWA must be opened from a **secure context** (https, or `localhost`) for the
browser crypto + offline install to work. Two easy ways:

### Option 1 — Host it on GitHub Pages (recommended; works anywhere after first load)
1. Put this folder in a GitHub repo and enable **GitHub Pages** (see the deep
   dive below — it's more than just pushing the files).
2. Open the Pages URL (`https://<user>.github.io/<repo>/`) in **Chrome** on the phone.
3. Menu (⋮) → **Add to Home screen / Install app**.
4. Launch from the icon. It now runs **offline** — no internet needed again.

### Option 2 — Serve from your PC (for testing / use on home Wi-Fi)
```bash
cd pass_manager_mobile
python3 -m http.server 8099
```
On the phone (same Wi-Fi) open `http://<PC-LAN-IP>:8099`. Note: some browsers
restrict `crypto.subtle` to https; if so, use Option 1 or a tunnel that gives
https (e.g. Tailscale Serve).

---

## GitHub Pages — everything to know

> Future-you, this section exists so you don't have to relearn all of this. Here
> is the whole picture in one place.

### Pushing to a branch is NOT the same as a running app
Putting these files on GitHub (any branch) only **stores the code**. GitHub shows
it as text/files; it does **not** run `index.html` as a website. Opening a file on
github.com — or its "raw" link — will **not** work as the app (wrong content type,
not a secure origin, the service worker won't register). Storage ≠ a usable app.

### What GitHub Pages actually is
GitHub Pages is a **free feature inside your repo** that serves these static files
as a real **https website** at:

```
https://<your-username>.github.io/<repo-name>/
```

That URL is a proper secure origin, so the browser crypto works, the PWA installs,
and after the first load it runs **fully offline** from the home-screen icon.
Pages publishes from a **branch/folder you choose** (e.g. a `gh-pages` branch, or
`main` → `/root` or `/docs`) — so "serve it from a branch" is exactly right, you
just have to flip the Pages switch so that branch gets *published*, not just stored.

### Public vs private (the part you asked about)
- On the **free** GitHub plan, Pages only serves from a **PUBLIC** repo.
  (Publishing Pages from a *private* repo needs a paid plan — Pro/Team.)
- **You can switch the repo back to private after installing**, and the installed
  app **keeps working** — the service worker already cached every file onto the
  phone, so it loads from the phone, not from GitHub. ✅
- The catch: while the repo is private, the github.io URL goes **dark**. You only
  need it live again at **install/update time**, specifically when you:
  - **reinstall** the app (new phone, cleared browser data, or removed it), or
  - want to **pull a code update** onto the phone.
  In those cases, flip the repo **public for a few minutes**, install/update, then
  flip it private again. Toggling public↔private is two clicks.
- **So the workflow is:** make it public → open on phone → Add to Home screen →
  switch repo to private. Daily use never needs the repo public.

### Is it safe to make a password app's repo public?
Yes. What becomes public is **only the code** — there are **no passwords, no keys,
no vault data** in it. Your entries/encrypted vault live **only in the phone's
storage**, and your **phrase is never stored or sent anywhere**. An open-source
generator is normal and even reassuring (anyone can verify it isn't phoning home).

### Fonts are bundled locally (no external calls)
The app's fonts (Inter + JetBrains Mono) are **included in this repo** (`fonts/`)
and loaded from `css/fonts.css`. There is **no Google Fonts request** — the app
makes **zero external network calls**, so it is pixel-perfect offline and nothing
about your usage leaves the phone.

## First run

1. Open the app → **Create your master password**.
2. Enter a **phrase** + **site** → Preview or **Generate & Save**.
3. The vault lists your entries; tap a password to reveal, **Copy** to copy.

## Syncing to the PC (optional, later)

Generation never needs the PC. `store.js` already exposes `exportSnapshot()` and
`mergeSnapshot()` so a future "Sync" button can push the phone's notes/revisions
to the desktop app when it is reachable (same Wi-Fi or via Tailscale). The phone
is the source of truth and always works offline.

## Security notes

- Runs entirely on the phone; the phrase never leaves it and is never stored.
- The vault is encrypted at rest; locking/closing forgets the key.
- Forgetting the master password means the stored list can't be decrypted — but
  any password can still be re-derived from `phrase + site + revision`.
