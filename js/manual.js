/*
 * manual.js — the in-app manual (rendered into the Manual screen).
 * Kept as one HTML string so the app stays a no-build, offline static bundle.
 */
"use strict";

const MANUAL_HTML = `
<h1>Vault — Manual</h1>
<p class="lead">A deterministic password generator + manager that runs entirely on your
phone, fully offline. Same engine as the desktop app — same phrase gives the same password.</p>

<div class="toc">
  <a href="#m-idea">1. The core idea</a>
  <a href="#m-two-secrets">2. Two secrets</a>
  <a href="#m-generate">3. Generating a password</a>
  <a href="#m-rotate">4. Rotating (the yellow box)</a>
  <a href="#m-determinism">5. Why it's deterministic</a>
  <a href="#m-offline">6. Offline &amp; install</a>
  <a href="#m-sync">7. Syncing to your PC</a>
  <a href="#m-security">8. Security model</a>
  <a href="#m-edge">9. Edge cases &amp; gotchas</a>
  <a href="#m-backup">10. Backup: export to Excel</a>
  <a href="#m-recover">11. Recovery</a>
</div>

<h2 id="m-idea">1. The core idea</h2>
<p>You don't store the passwords you actually log in with — you <em>re-create</em> them on
demand. You memorise <strong>one phrase</strong>. The app turns
<code>phrase + site + revision</code> into a strong password with upper-case, lower-case,
digits and symbols. The same inputs always give the same output, so you never have to
remember the result — just the phrase.</p>

<h2 id="m-two-secrets">2. Two secrets (don't mix them up)</h2>
<p><strong>The phrase</strong> is what generates passwords. It is never stored anywhere —
you type it when you generate or rotate. <strong>The master password</strong> only locks
this app and encrypts the saved list on the phone. They are independent: changing the
master password does <em>not</em> change any generated password.</p>
<div class="note">Your generated passwords depend ONLY on the phrase, the site label and the
revision number — never on the master password. That's why the phone and PC produce
identical results.</div>

<h2 id="m-generate">3. Generating a password</h2>
<p>Enter your <strong>phrase</strong>, a <strong>site label</strong> (e.g. <code>gmail</code>),
optionally a username, and a length. Tap <strong>Preview</strong> to see it without saving, or
<strong>Generate &amp; Save</strong> to store it in the vault. Use the same site label spelling
every time — <code>gmail</code>, <code>Gmail</code> and <code> gmail </code> are treated the
same (trimmed + lower-cased), but <code>gmail.com</code> is a different label than
<code>gmail</code>.</p>

<h2 id="m-rotate">4. Rotating (the yellow box)</h2>
<p>Need a fresh password for a site (a breach, a forced reset)? Tap <strong>Rotate</strong> and
re-enter your phrase. The <em>revision</em> bumps by one and a brand-new password appears. Its
<span class="yellow-chip">notes box turns yellow</span> to remind you it still needs changing on
the real website. Once you've updated it there, tap <strong>✓ Mark updated</strong> and the box
goes white again.</p>

<h2 id="m-determinism">5. Why it's deterministic</h2>
<p>The engine is PBKDF2-HMAC-SHA256 (200,000 iterations) over a salt built from the site label
and revision: <code>pwgen|v1|&lt;site&gt;|rev&lt;n&gt;</code>. No randomness is ever mixed in.
The derived bytes are mapped onto the character set, and one character from each class
(upper/lower/digit/symbol) is forced into the result so complexity rules always pass. This is a
byte-for-byte match to the desktop's <code>core/crypto.py</code> — verified by test.</p>

<h2 id="m-offline">6. Offline &amp; install</h2>
<p>This app needs <strong>no internet</strong> to run. Install it once and it works on a plane:</p>
<ul>
  <li>Open the app's URL in <strong>Chrome</strong> on your phone.</li>
  <li>Menu (⋮) → <strong>Add to Home screen</strong> / <strong>Install app</strong>.</li>
  <li>Launch it from the icon — it opens full-screen like a native app and runs offline.</li>
</ul>
<p>Your data is stored in the phone's local storage, encrypted with your master password.</p>

<h2 id="m-sync">7. Syncing to your PC</h2>
<p>Generation never needs your PC. Syncing the <em>notes and revision numbers</em> back to the
desktop app is optional and happens only when you choose to — and only when the PC app is open
and reachable (same Wi-Fi, or via a private tunnel like Tailscale). The phone is the source of
truth: it always works offline, and pushes updates to the PC when you sync. If the PC is off,
nothing breaks — you just sync later.</p>

<h2 id="m-security">8. Security model</h2>
<ul>
  <li><strong>Phrase</strong>: never stored, never leaves the phone.</li>
  <li><strong>Master password</strong>: stored only as a one-way PBKDF2 verifier.</li>
  <li><strong>Saved vault</strong>: encrypted at rest with AES-GCM, key derived from your master
      password (separate salt from the verifier).</li>
  <li><strong>Locking</strong> or closing the app forgets the key from memory and re-locks.</li>
</ul>

<h2 id="m-edge">9. Edge cases &amp; gotchas</h2>
<table class="perm">
  <tr><th>Situation</th><th>What happens</th></tr>
  <tr><td>Same phrase + same site + same revision</td><td>Identical password, every time, on any device.</td></tr>
  <tr><td>Site typed with different case/spaces</td><td>Trimmed and lower-cased, so it still matches.</td></tr>
  <tr><td>Site spelled differently (gmail vs gmail.com)</td><td>Different label → different password. Be consistent.</td></tr>
  <tr><td>Change the length</td><td>Different password. Length is part of the recipe — keep it fixed per site.</td></tr>
  <tr><td>Forget the revision number</td><td>It's saved in the vault; the entry shows <code>rev n</code>.</td></tr>
  <tr><td>Forget the master password</td><td>Stored vault can't be decrypted — but you can re-derive any password from the phrase.</td></tr>
  <tr><td>Different phrase</td><td>Completely different passwords. A single character change "screws you up" by design.</td></tr>
</table>

<h2 id="m-backup">10. Backup: export to Excel (your failsafe)</h2>
<p>If you ever lose your phone, an export is your safety net. Tap <strong>⤓ Export</strong> in the
top bar to save your whole vault as a <strong>password-protected Excel file</strong>
(<code>.xlsx</code>), with the columns <em>Site, Username/Email, Length, Note, Password</em>.</p>
<p>Two passwords are involved, on purpose:</p>
<ul>
  <li><strong>Export password</strong> (the second password you set when creating the vault): you're
  asked for it <em>before</em> the file is created, so someone who grabs your unlocked phone can't
  quietly dump your passwords.</li>
  <li><strong>Master password</strong>: the file itself is encrypted with it. When you open the
  <code>.xlsx</code> in Excel, Google Sheets or LibreOffice, it prompts for your master password
  before showing anything.</li>
</ul>
<div class="note">Both passwords stay in your head — neither is ever written into the file or stored
on the phone. The phrase is never exported (it's never stored anywhere). Keep the file somewhere
safe: even if someone gets it, they still need your master password to read it. (Created your vault
before this feature existed? The first time you tap Export it asks you to set an export password.)</div>

<h2 id="m-recover">11. Recovery</h2>
<p>Lost the phone or cleared the browser data? As long as you remember your <strong>phrase</strong>,
the <strong>site labels</strong> and the <strong>revision numbers</strong>, every password can be
regenerated from scratch — they were never really "stored", just recomputed. Keeping the PC app in
sync gives you a second copy of the labels/revisions for exactly this reason.</p>

<a class="back" href="#" id="manual-back-bottom">← Back to the app</a>
`;

// Wire the bottom "Back" link after the manual is injected.
document.addEventListener("click", (e) => {
  if (e.target && e.target.id === "manual-back-bottom") {
    e.preventDefault();
    const target = (typeof _returnScreen !== "undefined") ? _returnScreen : "screen-app";
    document.querySelectorAll("section[id^='screen-']").forEach((s) => {
      s.hidden = (s.id !== target);
    });
    window.scrollTo(0, 0);
  }
});
