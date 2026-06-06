/*
 * crypto.js — the security core for the MOBILE app.
 * =================================================
 * This is a faithful JavaScript port of the desktop `core/crypto.py`.
 *
 * THE ONE RULE: derivePassword(phrase, site, revision, length, iterations) must
 * return the EXACT same string as the Python desktop app for the same inputs.
 * If it ever differs, the phone and PC would disagree on your passwords — so the
 * port is byte-for-byte identical and verified by test against Python output.
 *
 * It runs fully offline. It uses the browser's native Web Crypto (fast) when a
 * secure context is available, and falls back to a self-contained pure-JS
 * PBKDF2-HMAC-SHA256 so generation still works even from a bare file:// page.
 */
"use strict";

const PMCrypto = (function () {
  // Same character classes as the desktop. Order matters — do not reorder.
  const UPPER = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
  const LOWER = "abcdefghijklmnopqrstuvwxyz";
  const DIGIT = "0123456789";
  const SPECIAL = "!@#$%^&*()-_=+[]{};:,.?";
  const FULL = UPPER + LOWER + DIGIT + SPECIAL;
  const CLASSES = [UPPER, LOWER, DIGIT, SPECIAL];
  const enc = new TextEncoder();

  // ---------------------------------------------------------------------------
  // Pure-JS SHA-256 / HMAC / PBKDF2 (fallback when crypto.subtle is absent)
  // ---------------------------------------------------------------------------
  const K = new Uint32Array([
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1,
    0x923f82a4, 0xab1c5ed5, 0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3,
    0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174, 0xe49b69c1, 0xefbe4786,
    0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147,
    0x06ca6351, 0x14292967, 0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13,
    0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85, 0xa2bfe8a1, 0xa81a664b,
    0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a,
    0x5b9cca4f, 0x682e6ff3, 0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
    0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
  ]);
  const rotr = (x, n) => (x >>> n) | (x << (32 - n));

  function sha256(msg) {
    let h0 = 0x6a09e667, h1 = 0xbb67ae85, h2 = 0x3c6ef372, h3 = 0xa54ff53a;
    let h4 = 0x510e527f, h5 = 0x9b05688c, h6 = 0x1f83d9ab, h7 = 0x5be0cd19;
    const l = msg.length;
    const bitLen = l * 8;
    const withOne = l + 1;
    const pad = (56 - (withOne % 64) + 64) % 64;
    const total = withOne + pad + 8;
    const buf = new Uint8Array(total);
    buf.set(msg, 0);
    buf[l] = 0x80;
    const dv = new DataView(buf.buffer);
    dv.setUint32(total - 4, bitLen >>> 0, false);
    dv.setUint32(total - 8, Math.floor(bitLen / 0x100000000), false);
    const w = new Uint32Array(64);
    for (let i = 0; i < total; i += 64) {
      for (let t = 0; t < 16; t++) w[t] = dv.getUint32(i + t * 4, false);
      for (let t = 16; t < 64; t++) {
        const s0 = rotr(w[t - 15], 7) ^ rotr(w[t - 15], 18) ^ (w[t - 15] >>> 3);
        const s1 = rotr(w[t - 2], 17) ^ rotr(w[t - 2], 19) ^ (w[t - 2] >>> 10);
        w[t] = (w[t - 16] + s0 + w[t - 7] + s1) | 0;
      }
      let a = h0, b = h1, c = h2, d = h3, e = h4, f = h5, g = h6, h = h7;
      for (let t = 0; t < 64; t++) {
        const S1 = rotr(e, 6) ^ rotr(e, 11) ^ rotr(e, 25);
        const ch = (e & f) ^ (~e & g);
        const t1 = (h + S1 + ch + K[t] + w[t]) | 0;
        const S0 = rotr(a, 2) ^ rotr(a, 13) ^ rotr(a, 22);
        const maj = (a & b) ^ (a & c) ^ (b & c);
        const t2 = (S0 + maj) | 0;
        h = g; g = f; f = e; e = (d + t1) | 0;
        d = c; c = b; b = a; a = (t1 + t2) | 0;
      }
      h0 = (h0 + a) | 0; h1 = (h1 + b) | 0; h2 = (h2 + c) | 0; h3 = (h3 + d) | 0;
      h4 = (h4 + e) | 0; h5 = (h5 + f) | 0; h6 = (h6 + g) | 0; h7 = (h7 + h) | 0;
    }
    const out = new Uint8Array(32);
    const odv = new DataView(out.buffer);
    [h0, h1, h2, h3, h4, h5, h6, h7].forEach((hh, i) => odv.setUint32(i * 4, hh >>> 0, false));
    return out;
  }

  function concat(a, b) {
    const out = new Uint8Array(a.length + b.length);
    out.set(a, 0);
    out.set(b, a.length);
    return out;
  }

  function hmacSha256(key, msg) {
    const block = 64;
    let k = key;
    if (k.length > block) k = sha256(k);
    if (k.length < block) {
      const t = new Uint8Array(block);
      t.set(k);
      k = t;
    }
    const okey = new Uint8Array(block);
    const ikey = new Uint8Array(block);
    for (let i = 0; i < block; i++) {
      okey[i] = k[i] ^ 0x5c;
      ikey[i] = k[i] ^ 0x36;
    }
    return sha256(concat(okey, sha256(concat(ikey, msg))));
  }

  function pbkdf2Pure(pw, salt, iterations, dklen) {
    const hLen = 32;
    const blocks = Math.ceil(dklen / hLen);
    const out = new Uint8Array(blocks * hLen);
    for (let i = 1; i <= blocks; i++) {
      const intBlock = new Uint8Array(4);
      new DataView(intBlock.buffer).setUint32(0, i, false);
      let u = hmacSha256(pw, concat(salt, intBlock));
      const t = u.slice();
      for (let j = 1; j < iterations; j++) {
        u = hmacSha256(pw, u);
        for (let k = 0; k < hLen; k++) t[k] ^= u[k];
      }
      out.set(t, (i - 1) * hLen);
    }
    return out.slice(0, dklen);
  }

  // ---------------------------------------------------------------------------
  // PBKDF2 — native when possible, pure-JS otherwise. Returns Uint8Array(dklen).
  // ---------------------------------------------------------------------------
  async function pbkdf2(secretStr, saltBytes, iterations, dklen) {
    const pw = enc.encode(secretStr);
    const subtle = globalThis.crypto && globalThis.crypto.subtle;
    if (subtle) {
      const km = await subtle.importKey("raw", pw, { name: "PBKDF2" }, false, ["deriveBits"]);
      const bits = await subtle.deriveBits(
        { name: "PBKDF2", salt: saltBytes, iterations, hash: "SHA-256" },
        km, dklen * 8
      );
      return new Uint8Array(bits);
    }
    return pbkdf2Pure(pw, saltBytes, iterations, dklen);
  }

  // ---------------------------------------------------------------------------
  // derivePassword — the deterministic generator. MUST match core/crypto.py.
  // ---------------------------------------------------------------------------
  async function derivePassword(phrase, site, revision, length, iterations) {
    if (length < 8) length = 8;
    const normalisedSite = String(site).trim().toLowerCase();
    const salt = enc.encode(`pwgen|v1|${normalisedSite}|rev${parseInt(revision, 10)}`);
    const dklen = length + 8;
    const dk = await pbkdf2(phrase, salt, iterations, dklen);

    const out = new Array(length);
    for (let i = 0; i < length; i++) out[i] = FULL[dk[i] % FULL.length];

    const perm = new Array(length);
    for (let i = 0; i < length; i++) perm[i] = i;
    for (let i = length - 1; i > 0; i--) {
      const k = dk[(i * 7) % dklen] % (i + 1);
      const tmp = perm[i];
      perm[i] = perm[k];
      perm[k] = tmp;
    }

    const extra = dk.slice(length, length + 8);
    for (let idx = 0; idx < CLASSES.length; idx++) {
      const cls = CLASSES[idx];
      const pos = perm[idx];
      out[pos] = cls[extra[idx] % cls.length];
    }
    return out.join("");
  }

  // ---------------------------------------------------------------------------
  // Master password handling (mirror of hash_master / verify_master)
  // ---------------------------------------------------------------------------
  function bytesToHex(b) {
    return Array.from(b).map((x) => x.toString(16).padStart(2, "0")).join("");
  }
  function hexToBytes(h) {
    const out = new Uint8Array(h.length / 2);
    for (let i = 0; i < out.length; i++) out[i] = parseInt(h.substr(i * 2, 2), 16);
    return out;
  }
  function b64(bytes) {
    let s = "";
    for (const x of bytes) s += String.fromCharCode(x);
    return btoa(s);
  }
  function unb64(str) {
    const s = atob(str);
    const out = new Uint8Array(s.length);
    for (let i = 0; i < s.length; i++) out[i] = s.charCodeAt(i);
    return out;
  }

  async function hashMaster(master, saltBytes, iterations) {
    return await pbkdf2(master, saltBytes, iterations, 32);
  }
  // Constant-time-ish comparison (length-independent enough for a local app).
  async function verifyMaster(master, saltBytes, iterations, expectedBytes) {
    const cand = await hashMaster(master, saltBytes, iterations);
    if (cand.length !== expectedBytes.length) return false;
    let diff = 0;
    for (let i = 0; i < cand.length; i++) diff |= cand[i] ^ expectedBytes[i];
    return diff === 0;
  }

  // ---------------------------------------------------------------------------
  // Encryption at rest on the phone (AES-GCM via Web Crypto).
  // The key is derived from the master password with its own salt, so the stored
  // verifier can never be reused to decrypt the vault.
  // ---------------------------------------------------------------------------
  async function deriveAesKey(master, encSaltBytes, iterations) {
    const subtle = globalThis.crypto && globalThis.crypto.subtle;
    if (!subtle) throw new Error("This browser/context has no Web Crypto; open the app over https or localhost.");
    const raw = await pbkdf2(master, encSaltBytes, iterations, 32);
    return await subtle.importKey("raw", raw, { name: "AES-GCM" }, false, ["encrypt", "decrypt"]);
  }

  async function encryptJSON(aesKey, obj) {
    const subtle = globalThis.crypto.subtle;
    const iv = globalThis.crypto.getRandomValues(new Uint8Array(12));
    const data = enc.encode(JSON.stringify(obj));
    const ct = new Uint8Array(await subtle.encrypt({ name: "AES-GCM", iv }, aesKey, data));
    return b64(iv) + ":" + b64(ct);
  }

  async function decryptJSON(aesKey, blob) {
    const subtle = globalThis.crypto.subtle;
    const [ivPart, ctPart] = blob.split(":");
    const iv = unb64(ivPart);
    const ct = unb64(ctPart);
    const pt = await subtle.decrypt({ name: "AES-GCM", iv }, aesKey, ct);
    return JSON.parse(new TextDecoder().decode(pt));
  }

  function randomBytes(n) {
    return globalThis.crypto.getRandomValues(new Uint8Array(n));
  }

  return {
    derivePassword,
    hashMaster, verifyMaster,
    deriveAesKey, encryptJSON, decryptJSON,
    randomBytes, bytesToHex, hexToBytes, b64, unb64,
    hasSubtle: () => !!(globalThis.crypto && globalThis.crypto.subtle),
  };
})();

// Export for Node-based testing; harmless in the browser.
if (typeof module !== "undefined" && module.exports) module.exports = PMCrypto;
