/*
 * export.js — encrypted Excel (.xlsx) export, the "failsafe" backup.
 * ==================================================================
 * Builds a REAL Microsoft-Office password-protected spreadsheet entirely in the
 * phone, offline, with no libraries. Opening the file in Excel / LibreOffice /
 * Google Sheets prompts for the master password — exactly the file you'd get
 * from Excel's "Encrypt with Password".
 *
 * Two layers, both standard:
 *   1. A normal .xlsx  = a ZIP of OOXML XML parts (built here, no compression).
 *   2. MS-OFFCRYPTO "agile encryption" (ECMA-376) wrapping that .xlsx inside an
 *      OLE2 / Compound File Binary (CFB) container, encrypted with the master
 *      password. SHA-512 + AES-256-CBC + HMAC-SHA512, all via Web Crypto.
 *
 * The master password is NEVER stored — it is used here only as the encryption
 * key for the file and is required to open the file afterwards.
 *
 * Verified end-to-end against msoffcrypto-tool + openpyxl (see docs): the file
 * this produces decrypts with the master password and reads as a valid sheet.
 */
"use strict";

const PMExport = (function () {
  const te = new TextEncoder();
  const subtleOf = () => (globalThis.crypto && globalThis.crypto.subtle);

  // ---- little-endian / byte helpers -----------------------------------------
  function concatBytes(...arrs) {
    let n = 0;
    for (const a of arrs) n += a.length;
    const out = new Uint8Array(n);
    let o = 0;
    for (const a of arrs) { out.set(a, o); o += a.length; }
    return out;
  }
  function u16le(n) { const b = new Uint8Array(2); new DataView(b.buffer).setUint16(0, n & 0xffff, true); return b; }
  function u32le(n) { const b = new Uint8Array(4); new DataView(b.buffer).setUint32(0, n >>> 0, true); return b; }
  function u64le(n) {
    const b = new Uint8Array(8); const dv = new DataView(b.buffer);
    dv.setUint32(0, n >>> 0, true);
    dv.setUint32(4, Math.floor(n / 0x100000000) >>> 0, true);
    return b;
  }
  function utf16le(str) {
    const b = new Uint8Array(str.length * 2); const dv = new DataView(b.buffer);
    for (let i = 0; i < str.length; i++) dv.setUint16(i * 2, str.charCodeAt(i), true);
    return b;
  }
  function b64(bytes) { let s = ""; for (const x of bytes) s += String.fromCharCode(x); return btoa(s); }
  function xmlEsc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&apos;" }[c]));
  }

  // ---- pure-JS SHA-512 (synchronous) ----------------------------------------
  // The agile-encryption KDF spins SHA-512 100,000 times. Doing that with the
  // async Web Crypto digest means 100k awaited microtasks (~17s). A synchronous
  // SHA-512 (32-bit hi/lo word pairs) does the same work in a fraction of that.
  const KH = new Uint32Array([
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
    0xca273ece, 0xd186b8c7, 0xeada7dd6, 0xf57d4f7f, 0x06f067aa, 0x0a637dc5, 0x113f9804, 0x1b710b35,
    0x28db77f5, 0x32caab7b, 0x3c9ebe0a, 0x431d67c4, 0x4cc5d4be, 0x597f299c, 0x5fcb6fab, 0x6c44198c,
  ]);
  const KL = new Uint32Array([
    0xd728ae22, 0x23ef65cd, 0xec4d3b2f, 0x8189dbbc, 0xf348b538, 0xb605d019, 0xaf194f9b, 0xda6d8118,
    0xa3030242, 0x45706fbe, 0x4ee4b28c, 0xd5ffb4e2, 0xf27b896f, 0x3b1696b1, 0x25c71235, 0xcf692694,
    0x9ef14ad2, 0x384f25e3, 0x8b8cd5b5, 0x77ac9c65, 0x592b0275, 0x6ea6e483, 0xbd41fbd4, 0x831153b5,
    0xee66dfab, 0x2db43210, 0x98fb213f, 0xbeef0ee4, 0x3da88fc2, 0x930aa725, 0xe003826f, 0x0a0e6e70,
    0x46d22ffc, 0x5c26c926, 0x5ac42aed, 0x9d95b3df, 0x8baf63de, 0x3c77b2a8, 0x47edaee6, 0x1482353b,
    0x4cf10364, 0xbc423001, 0xd0f89791, 0x0654be30, 0xd6ef5218, 0x5565a910, 0x5771202a, 0x32bbd1b8,
    0xb8d2d0c8, 0x5141ab53, 0xdf8eeb99, 0xe19b48a8, 0xc5c95a63, 0xe3418acb, 0x7763e373, 0xd6b2b8a3,
    0x5defb2fc, 0x43172f60, 0xa1f0ab72, 0x1a6439ec, 0x23631e28, 0xde82bde9, 0xb2c67915, 0xe372532b,
    0xea26619c, 0x21c0c207, 0xcde0eb1e, 0xee6ed178, 0x72176fba, 0xa2c898a6, 0xbef90dae, 0x131c471b,
    0x23047d84, 0x40c72493, 0x15c9bebc, 0x9c100d4c, 0xcb3e42b6, 0xfc657e2a, 0x3ad6faec, 0x4a475817,
  ]);
  const W_H = new Uint32Array(80), W_L = new Uint32Array(80);

  function sha512(msg) {
    let H0H = 0x6a09e667, H0L = 0xf3bcc908, H1H = 0xbb67ae85, H1L = 0x84caa73b,
        H2H = 0x3c6ef372, H2L = 0xfe94f82b, H3H = 0xa54ff53a, H3L = 0x5f1d36f1,
        H4H = 0x510e527f, H4L = 0xade682d1, H5H = 0x9b05688c, H5L = 0x2b3e6c1f,
        H6H = 0x1f83d9ab, H6L = 0xfb41bd6b, H7H = 0x5be0cd19, H7L = 0x137e2179;

    const l = msg.length;
    const withOne = l + 1;
    const k = (128 - ((withOne + 16) % 128)) % 128;
    const total = withOne + k + 16;
    const buf = new Uint8Array(total);
    buf.set(msg, 0); buf[l] = 0x80;
    const dv = new DataView(buf.buffer);
    dv.setUint32(total - 8, Math.floor(l / 0x20000000) >>> 0, false); // bit length high
    dv.setUint32(total - 4, (l * 8) >>> 0, false);                    // bit length low

    for (let off = 0; off < total; off += 128) {
      for (let t = 0; t < 16; t++) {
        W_H[t] = dv.getUint32(off + t * 8, false);
        W_L[t] = dv.getUint32(off + t * 8 + 4, false);
      }
      for (let t = 16; t < 80; t++) {
        let xH = W_H[t - 15], xL = W_L[t - 15];
        const s0H = ((xH >>> 1) | (xL << 31)) ^ ((xH >>> 8) | (xL << 24)) ^ (xH >>> 7);
        const s0L = ((xL >>> 1) | (xH << 31)) ^ ((xL >>> 8) | (xH << 24)) ^ ((xL >>> 7) | (xH << 25));
        xH = W_H[t - 2]; xL = W_L[t - 2];
        const s1H = ((xH >>> 19) | (xL << 13)) ^ ((xL >>> 29) | (xH << 3)) ^ (xH >>> 6);
        const s1L = ((xL >>> 19) | (xH << 13)) ^ ((xH >>> 29) | (xL << 3)) ^ ((xL >>> 6) | (xH << 26));
        let lo = (s1L >>> 0) + (W_L[t - 7] >>> 0) + (s0L >>> 0) + (W_L[t - 16] >>> 0);
        const hi = (s1H >>> 0) + (W_H[t - 7] >>> 0) + (s0H >>> 0) + (W_H[t - 16] >>> 0) + Math.floor(lo / 0x100000000);
        W_L[t] = lo >>> 0; W_H[t] = hi >>> 0;
      }

      let aH = H0H, aL = H0L, bH = H1H, bL = H1L, cH = H2H, cL = H2L, dH = H3H, dL = H3L,
          eH = H4H, eL = H4L, fH = H5H, fL = H5L, gH = H6H, gL = H6L, hH = H7H, hL = H7L;

      for (let t = 0; t < 80; t++) {
        const S1H = ((eH >>> 14) | (eL << 18)) ^ ((eH >>> 18) | (eL << 14)) ^ ((eL >>> 9) | (eH << 23));
        const S1L = ((eL >>> 14) | (eH << 18)) ^ ((eL >>> 18) | (eH << 14)) ^ ((eH >>> 9) | (eL << 23));
        const chH = (eH & fH) ^ (~eH & gH);
        const chL = (eL & fL) ^ (~eL & gL);
        let t1lo = (hL >>> 0) + (S1L >>> 0) + (chL >>> 0) + (KL[t] >>> 0) + (W_L[t] >>> 0);
        let t1hi = ((hH >>> 0) + (S1H >>> 0) + (chH >>> 0) + (KH[t] >>> 0) + (W_H[t] >>> 0) + Math.floor(t1lo / 0x100000000)) >>> 0;
        t1lo = t1lo >>> 0;
        const S0H = ((aH >>> 28) | (aL << 4)) ^ ((aL >>> 2) | (aH << 30)) ^ ((aL >>> 7) | (aH << 25));
        const S0L = ((aL >>> 28) | (aH << 4)) ^ ((aH >>> 2) | (aL << 30)) ^ ((aH >>> 7) | (aL << 25));
        const majH = (aH & bH) ^ (aH & cH) ^ (bH & cH);
        const majL = (aL & bL) ^ (aL & cL) ^ (bL & cL);
        let t2lo = (S0L >>> 0) + (majL >>> 0);
        const t2hi = ((S0H >>> 0) + (majH >>> 0) + Math.floor(t2lo / 0x100000000)) >>> 0;
        t2lo = t2lo >>> 0;

        hH = gH; hL = gL; gH = fH; gL = fL; fH = eH; fL = eL;
        let elo = (dL >>> 0) + t1lo;
        eH = ((dH >>> 0) + t1hi + Math.floor(elo / 0x100000000)) >>> 0; eL = elo >>> 0;
        dH = cH; dL = cL; cH = bH; cL = bL; bH = aH; bL = aL;
        let alo = t1lo + t2lo;
        aH = (t1hi + t2hi + Math.floor(alo / 0x100000000)) >>> 0; aL = alo >>> 0;
      }

      let x;
      x = (H0L >>> 0) + (aL >>> 0); H0L = x >>> 0; H0H = (H0H + aH + Math.floor(x / 0x100000000)) >>> 0;
      x = (H1L >>> 0) + (bL >>> 0); H1L = x >>> 0; H1H = (H1H + bH + Math.floor(x / 0x100000000)) >>> 0;
      x = (H2L >>> 0) + (cL >>> 0); H2L = x >>> 0; H2H = (H2H + cH + Math.floor(x / 0x100000000)) >>> 0;
      x = (H3L >>> 0) + (dL >>> 0); H3L = x >>> 0; H3H = (H3H + dH + Math.floor(x / 0x100000000)) >>> 0;
      x = (H4L >>> 0) + (eL >>> 0); H4L = x >>> 0; H4H = (H4H + eH + Math.floor(x / 0x100000000)) >>> 0;
      x = (H5L >>> 0) + (fL >>> 0); H5L = x >>> 0; H5H = (H5H + fH + Math.floor(x / 0x100000000)) >>> 0;
      x = (H6L >>> 0) + (gL >>> 0); H6L = x >>> 0; H6H = (H6H + gH + Math.floor(x / 0x100000000)) >>> 0;
      x = (H7L >>> 0) + (hL >>> 0); H7L = x >>> 0; H7H = (H7H + hH + Math.floor(x / 0x100000000)) >>> 0;
    }

    const out = new Uint8Array(64), o = new DataView(out.buffer);
    o.setUint32(0, H0H, false); o.setUint32(4, H0L, false); o.setUint32(8, H1H, false); o.setUint32(12, H1L, false);
    o.setUint32(16, H2H, false); o.setUint32(20, H2L, false); o.setUint32(24, H3H, false); o.setUint32(28, H3L, false);
    o.setUint32(32, H4H, false); o.setUint32(36, H4L, false); o.setUint32(40, H5H, false); o.setUint32(44, H5L, false);
    o.setUint32(48, H6H, false); o.setUint32(52, H6L, false); o.setUint32(56, H7H, false); o.setUint32(60, H7L, false);
    return out;
  }

  // ---- Web Crypto wrappers (AES + HMAC stay native; few calls) --------------
  function rand(n) { return globalThis.crypto.getRandomValues(new Uint8Array(n)); }
  async function hmacSha512(keyBytes, msg) {
    const k = await subtleOf().importKey("raw", keyBytes, { name: "HMAC", hash: "SHA-512" }, false, ["sign"]);
    return new Uint8Array(await subtleOf().sign("HMAC", k, msg));
  }
  // AES-256-CBC with NO padding. Web Crypto always PKCS#7-pads, so we feed data
  // that is already a multiple of 16 and drop the extra padding block it appends
  // (CBC block i depends only on blocks 1..i, so the prefix is the unpadded CT).
  async function aesCbcNoPad(keyBytes, iv, data) {
    const key = await subtleOf().importKey("raw", keyBytes, { name: "AES-CBC" }, false, ["encrypt"]);
    const full = new Uint8Array(await subtleOf().encrypt({ name: "AES-CBC", iv }, key, data));
    return full.slice(0, data.length);
  }

  // ===========================================================================
  // 1) Build a minimal, valid .xlsx (ZIP of OOXML parts, stored uncompressed)
  // ===========================================================================
  let CRC_TABLE = null;
  function crc32(buf) {
    if (!CRC_TABLE) {
      CRC_TABLE = new Uint32Array(256);
      for (let n = 0; n < 256; n++) {
        let c = n;
        for (let k = 0; k < 8; k++) c = (c & 1) ? (0xEDB88320 ^ (c >>> 1)) : (c >>> 1);
        CRC_TABLE[n] = c >>> 0;
      }
    }
    let c = 0xFFFFFFFF;
    for (let i = 0; i < buf.length; i++) c = CRC_TABLE[(c ^ buf[i]) & 0xFF] ^ (c >>> 8);
    return (c ^ 0xFFFFFFFF) >>> 0;
  }

  function zipStore(files) {
    const local = [], central = [];
    let offset = 0;
    for (const f of files) {
      const name = te.encode(f.name);
      const data = f.data;
      const crc = crc32(data);
      const lh = new Uint8Array(30 + name.length);
      const ld = new DataView(lh.buffer);
      ld.setUint32(0, 0x04034b50, true); ld.setUint16(4, 20, true); ld.setUint16(6, 0, true);
      ld.setUint16(8, 0, true); ld.setUint16(10, 0, true); ld.setUint16(12, 0x21, true); // 1980-01-01
      ld.setUint32(14, crc, true); ld.setUint32(18, data.length, true); ld.setUint32(22, data.length, true);
      ld.setUint16(26, name.length, true); ld.setUint16(28, 0, true);
      lh.set(name, 30);
      local.push(lh, data);

      const ce = new Uint8Array(46 + name.length);
      const cd = new DataView(ce.buffer);
      cd.setUint32(0, 0x02014b50, true); cd.setUint16(4, 20, true); cd.setUint16(6, 20, true);
      cd.setUint16(8, 0, true); cd.setUint16(10, 0, true); cd.setUint16(12, 0, true); cd.setUint16(14, 0x21, true);
      cd.setUint32(16, crc, true); cd.setUint32(20, data.length, true); cd.setUint32(24, data.length, true);
      cd.setUint16(28, name.length, true); cd.setUint16(30, 0, true); cd.setUint16(32, 0, true);
      cd.setUint16(34, 0, true); cd.setUint16(36, 0, true); cd.setUint32(38, 0, true); cd.setUint32(42, offset, true);
      ce.set(name, 46);
      central.push(ce);
      offset += lh.length + data.length;
    }
    const cdir = concatBytes(...central);
    const eocd = new Uint8Array(22);
    const ev = new DataView(eocd.buffer);
    ev.setUint32(0, 0x06054b50, true); ev.setUint16(4, 0, true); ev.setUint16(6, 0, true);
    ev.setUint16(8, files.length, true); ev.setUint16(10, files.length, true);
    ev.setUint32(12, cdir.length, true); ev.setUint32(16, offset, true); ev.setUint16(20, 0, true);
    return concatBytes(...local, cdir, eocd);
  }

  function colLetter(i) { // 0-based -> A, B, ... Z, AA, ...
    let s = ""; i++;
    while (i > 0) { const r = (i - 1) % 26; s = String.fromCharCode(65 + r) + s; i = Math.floor((i - 1) / 26); }
    return s;
  }
  const textCell = (ref, v) => `<c r="${ref}" t="inlineStr"><is><t xml:space="preserve">${xmlEsc(v)}</t></is></c>`;
  const numCell = (ref, v) => `<c r="${ref}"><v>${Number(v) || 0}</v></c>`;

  function buildXlsx(rows) {
    const headers = ["Site", "Username / Email", "Length", "Note", "Password"];
    let body = `<row r="1">${headers.map((h, i) => textCell(colLetter(i) + "1", h)).join("")}</row>`;
    rows.forEach((r, ri) => {
      const R = ri + 2;
      body += `<row r="${R}">` +
        textCell(colLetter(0) + R, r.site) +
        textCell(colLetter(1) + R, r.email) +
        numCell(colLetter(2) + R, r.length) +
        textCell(colLetter(3) + R, r.where) +
        textCell(colLetter(4) + R, r.password) +
        `</row>`;
    });

    const sheet = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>` +
      `<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">` +
      `<sheetData>${body}</sheetData></worksheet>`;

    const contentTypes = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>` +
      `<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">` +
      `<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>` +
      `<Default Extension="xml" ContentType="application/xml"/>` +
      `<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>` +
      `<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>` +
      `<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>` +
      `</Types>`;

    const rels = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>` +
      `<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">` +
      `<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>` +
      `</Relationships>`;

    const workbook = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>` +
      `<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" ` +
      `xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">` +
      `<sheets><sheet name="Vault" sheetId="1" r:id="rId1"/></sheets></workbook>`;

    const wbRels = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>` +
      `<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">` +
      `<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>` +
      `<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>` +
      `</Relationships>`;

    const styles = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>` +
      `<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">` +
      `<fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts>` +
      `<fills count="1"><fill><patternFill patternType="none"/></fill></fills>` +
      `<borders count="1"><border/></borders>` +
      `<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>` +
      `<cellXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/></cellXfs>` +
      `<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>` +
      `</styleSheet>`;

    return zipStore([
      { name: "[Content_Types].xml", data: te.encode(contentTypes) },
      { name: "_rels/.rels", data: te.encode(rels) },
      { name: "xl/workbook.xml", data: te.encode(workbook) },
      { name: "xl/_rels/workbook.xml.rels", data: te.encode(wbRels) },
      { name: "xl/styles.xml", data: te.encode(styles) },
      { name: "xl/worksheets/sheet1.xml", data: te.encode(sheet) },
    ]);
  }

  // ===========================================================================
  // 2) MS-OFFCRYPTO agile encryption (ECMA-376). Returns the two CFB streams.
  // ===========================================================================
  const BK_VERIFIER_INPUT = [0xfe, 0xa7, 0xd2, 0x76, 0x3b, 0x4b, 0x9e, 0x79];
  const BK_VERIFIER_VALUE = [0xd7, 0xaa, 0x0f, 0x6d, 0x30, 0x61, 0x34, 0x4e];
  const BK_KEY_VALUE = [0x14, 0x6e, 0x0b, 0xe7, 0xab, 0xac, 0xd0, 0xd6];
  const BK_HMAC_KEY = [0x5f, 0xb2, 0xad, 0x01, 0x0c, 0xb9, 0xe1, 0xf6];
  const BK_HMAC_VALUE = [0xa0, 0x67, 0x7f, 0x02, 0xb2, 0x2c, 0x84, 0x33];
  const SPIN_COUNT = 100000;
  const SEGMENT = 4096;

  async function encryptAgile(pkg, password) {
    const keyDataSalt = rand(16);   // salt for package + integrity IVs
    const keySalt = rand(16);       // salt for the password key-encryptor

    // Password -> base hash (SHA-512, spun SPIN_COUNT times). Synchronous: no
    // per-iteration microtask, so 100k spins finish in well under a second.
    let h = sha512(concatBytes(keySalt, utf16le(password)));
    for (let i = 0; i < SPIN_COUNT; i++) h = sha512(concatBytes(u32le(i), h));
    const baseHash = h;
    const deriveKey = (blockKey) => sha512(concatBytes(baseHash, new Uint8Array(blockKey))).slice(0, 32);

    // The real package key, plus the password-encrypted verifier proving the pw.
    const secretKey = rand(32);
    const verifier = rand(16);
    const encVerifierInput = await aesCbcNoPad(deriveKey(BK_VERIFIER_INPUT), keySalt, verifier);
    const encVerifierValue = await aesCbcNoPad(deriveKey(BK_VERIFIER_VALUE), keySalt, sha512(verifier));
    const encKeyValue = await aesCbcNoPad(deriveKey(BK_KEY_VALUE), keySalt, secretKey);

    // Encrypt the package in 4096-byte CBC segments, each with its own IV.
    const segs = [];
    for (let off = 0, i = 0; off < pkg.length; off += SEGMENT, i++) {
      let chunk = pkg.slice(off, off + SEGMENT);
      if (chunk.length % 16 !== 0) {
        const padded = new Uint8Array(Math.ceil(chunk.length / 16) * 16);
        padded.set(chunk); chunk = padded;
      }
      const iv = sha512(concatBytes(keyDataSalt, u32le(i))).slice(0, 16);
      segs.push(await aesCbcNoPad(secretKey, iv, chunk));
    }
    const encryptedPackage = concatBytes(u64le(pkg.length), ...segs);

    // Data integrity: HMAC-SHA512 over the whole EncryptedPackage stream.
    const hmacKey = rand(64);
    const ivKey = sha512(concatBytes(keyDataSalt, new Uint8Array(BK_HMAC_KEY))).slice(0, 16);
    const encHmacKey = await aesCbcNoPad(secretKey, ivKey, hmacKey);
    const hmacValue = await hmacSha512(hmacKey, encryptedPackage);
    const ivVal = sha512(concatBytes(keyDataSalt, new Uint8Array(BK_HMAC_VALUE))).slice(0, 16);
    const encHmacValue = await aesCbcNoPad(secretKey, ivVal, hmacValue);

    const xml = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>` +
      `<encryption xmlns="http://schemas.microsoft.com/office/2006/encryption" ` +
      `xmlns:p="http://schemas.microsoft.com/office/2006/keyEncryptor/password">` +
      `<keyData saltSize="16" blockSize="16" keyBits="256" hashSize="64" ` +
      `cipherAlgorithm="AES" cipherChaining="ChainingModeCBC" hashAlgorithm="SHA512" ` +
      `saltValue="${b64(keyDataSalt)}"/>` +
      `<dataIntegrity encryptedHmacKey="${b64(encHmacKey)}" encryptedHmacValue="${b64(encHmacValue)}"/>` +
      `<keyEncryptors><keyEncryptor uri="http://schemas.microsoft.com/office/2006/keyEncryptor/password">` +
      `<p:encryptedKey spinCount="${SPIN_COUNT}" saltSize="16" blockSize="16" keyBits="256" hashSize="64" ` +
      `cipherAlgorithm="AES" cipherChaining="ChainingModeCBC" hashAlgorithm="SHA512" ` +
      `saltValue="${b64(keySalt)}" ` +
      `encryptedVerifierHashInput="${b64(encVerifierInput)}" ` +
      `encryptedVerifierHashValue="${b64(encVerifierValue)}" ` +
      `encryptedKeyValue="${b64(encKeyValue)}"/>` +
      `</keyEncryptor></keyEncryptors></encryption>`;

    const xmlBytes = te.encode(xml);
    const info = new Uint8Array(8 + xmlBytes.length);
    const idv = new DataView(info.buffer);
    idv.setUint16(0, 0x0004, true);   // version major
    idv.setUint16(2, 0x0004, true);   // version minor
    idv.setUint32(4, 0x40, true);     // flags: fAgile
    info.set(xmlBytes, 8);

    return { encryptionInfo: info, encryptedPackage };
  }

  // ===========================================================================
  // 3) OLE2 / Compound File Binary container (v3, 512-byte sectors)
  // ===========================================================================
  function buildCFB(streams) {
    const SECTOR = 512, MINI = 64, CUTOFF = 4096;
    const ENDOFCHAIN = 0xFFFFFFFE, FREESECT = 0xFFFFFFFF, FATSECT = 0xFFFFFFFD, NOSTREAM = 0xFFFFFFFF;

    // Mini stream (for streams < 4096 bytes): collect chunks + a mini-FAT chain.
    const miniChunks = []; const miniFAT = []; let miniCount = 0;
    function addMini(data) {
      const nSec = Math.ceil(data.length / MINI);
      const start = miniCount;
      for (let i = 0; i < nSec; i++) miniFAT.push(i === nSec - 1 ? ENDOFCHAIN : start + i + 1);
      const padded = new Uint8Array(nSec * MINI); padded.set(data);
      miniChunks.push(padded); miniCount += nSec;
      return start;
    }
    const placement = streams.map((s) =>
      s.data.length >= CUTOFF ? { stream: s, mini: false }
        : { stream: s, mini: true, miniStart: addMini(s.data) });

    const miniContainer = concatBytes(...miniChunks);
    let miniFatBytes = new Uint8Array(0);
    if (miniFAT.length) {
      miniFatBytes = new Uint8Array(Math.ceil(miniFAT.length * 4 / SECTOR) * SECTOR).fill(0xFF);
      const dv = new DataView(miniFatBytes.buffer);
      miniFAT.forEach((v, i) => dv.setUint32(i * 4, v >>> 0, true));
    }

    // Big (FAT) sectors, in file order: directory, mini-FAT, mini container, big streams.
    const nEntries = streams.length + 1;
    const dirLen = Math.ceil(nEntries * 128 / SECTOR) * SECTOR;
    const bigList = [{ key: "dir", len: dirLen }];
    if (miniFatBytes.length) bigList.push({ key: "minifat", len: miniFatBytes.length });
    if (miniContainer.length) bigList.push({ key: "minicont", len: Math.ceil(miniContainer.length / SECTOR) * SECTOR });
    placement.forEach((p, idx) => {
      if (!p.mini) bigList.push({ key: "big" + idx, len: Math.ceil(p.stream.data.length / SECTOR) * SECTOR, idx });
    });

    let sec = 0; const startOf = {};
    for (const b of bigList) { b.start = sec; b.nsec = b.len / SECTOR; startOf[b.key] = b.start; sec += b.nsec; }
    const dataSectors = sec;

    const firstDir = startOf["dir"];
    const firstMiniFat = "minifat" in startOf ? startOf["minifat"] : ENDOFCHAIN;
    const miniFatCount = "minifat" in startOf ? bigList.find((b) => b.key === "minifat").nsec : 0;
    const rootStart = "minicont" in startOf ? startOf["minicont"] : ENDOFCHAIN;

    // FAT sectors needed (placed after the data sectors).
    let nFat = 1;
    while (nFat * (SECTOR / 4) < dataSectors + nFat) nFat++;
    const fatStart = dataSectors;
    const total = dataSectors + nFat;

    const fat = new Uint32Array(total).fill(FREESECT);
    for (const b of bigList) for (let i = 0; i < b.nsec; i++) fat[b.start + i] = (i === b.nsec - 1) ? ENDOFCHAIN : b.start + i + 1;
    for (let i = 0; i < nFat; i++) fat[fatStart + i] = FATSECT;

    // Directory: Root + one entry per stream, linked as a balanced BST.
    const dir = new Uint8Array(dirLen);
    const dv = new DataView(dir.buffer);
    const slots = dirLen / 128;
    for (let i = 0; i < slots; i++) {
      const off = i * 128;
      dv.setUint32(off + 68, NOSTREAM, true);
      dv.setUint32(off + 72, NOSTREAM, true);
      dv.setUint32(off + 76, NOSTREAM, true);
    }
    function writeEntry(i, name, type, left, right, child, start, size) {
      const off = i * 128;
      for (let c = 0; c < name.length; c++) dv.setUint16(off + c * 2, name.charCodeAt(c), true);
      dv.setUint16(off + 64, (name.length + 1) * 2, true);
      dir[off + 66] = type; dir[off + 67] = 1; // black
      dv.setUint32(off + 68, left >>> 0, true);
      dv.setUint32(off + 72, right >>> 0, true);
      dv.setUint32(off + 76, child >>> 0, true);
      dv.setUint32(off + 116, start >>> 0, true);
      dv.setUint32(off + 120, size >>> 0, true);
      dv.setUint32(off + 124, Math.floor(size / 0x100000000) >>> 0, true);
    }
    // CFB name ordering: shorter name first, else case-insensitive UTF-16.
    const cmp = (a, b) => (a.length !== b.length) ? a.length - b.length
      : (a.toUpperCase() < b.toUpperCase() ? -1 : a.toUpperCase() > b.toUpperCase() ? 1 : 0);
    const order = streams.map((s, idx) => ({ id: idx + 1, name: s.name, left: NOSTREAM, right: NOSTREAM }))
      .sort((x, y) => cmp(x.name, y.name));
    const byId = new Map(order.map((o) => [o.id, o]));
    function build(lo, hi) {
      if (lo > hi) return NOSTREAM;
      const mid = (lo + hi) >> 1, node = order[mid];
      node.left = build(lo, mid - 1); node.right = build(mid + 1, hi);
      return node.id;
    }
    const rootChild = build(0, order.length - 1);

    writeEntry(0, "Root Entry", 5, NOSTREAM, NOSTREAM, rootChild, rootStart, miniContainer.length);
    placement.forEach((p, idx) => {
      const node = byId.get(idx + 1);
      const start = p.mini ? p.miniStart : startOf["big" + idx];
      writeEntry(idx + 1, p.stream.name, 2, node.left, node.right, NOSTREAM, start, p.stream.data.length);
    });

    // Assemble the sectors backing each big-list entry.
    function dataFor(b) {
      if (b.key === "dir") return dir;
      if (b.key === "minifat") return miniFatBytes;
      if (b.key === "minicont") { const x = new Uint8Array(b.len); x.set(miniContainer); return x; }
      const x = new Uint8Array(b.len); x.set(placement[b.idx].stream.data); return x;
    }

    const fatBytes = new Uint8Array(nFat * SECTOR).fill(0xFF);
    const fdv = new DataView(fatBytes.buffer);
    for (let i = 0; i < total; i++) fdv.setUint32(i * 4, fat[i] >>> 0, true);

    const header = new Uint8Array(512);
    const hdv = new DataView(header.buffer);
    [0xD0, 0xCF, 0x11, 0xE0, 0xA1, 0xB1, 0x1A, 0xE1].forEach((v, i) => (header[i] = v));
    hdv.setUint16(24, 0x003E, true); // minor version
    hdv.setUint16(26, 0x0003, true); // major version (v3)
    hdv.setUint16(28, 0xFFFE, true); // little-endian
    hdv.setUint16(30, 0x0009, true); // sector shift => 512
    hdv.setUint16(32, 0x0006, true); // mini sector shift => 64
    hdv.setUint32(44, nFat, true);
    hdv.setUint32(48, firstDir, true);
    hdv.setUint32(56, CUTOFF, true);
    hdv.setUint32(60, firstMiniFat >>> 0, true);
    hdv.setUint32(64, miniFatCount, true);
    hdv.setUint32(68, ENDOFCHAIN, true); // first DIFAT sector (none)
    hdv.setUint32(72, 0, true);          // DIFAT sector count
    for (let i = 0; i < 109; i++) hdv.setUint32(76 + i * 4, (i < nFat ? fatStart + i : FREESECT) >>> 0, true);

    const parts = [header];
    for (const b of bigList) parts.push(dataFor(b));
    parts.push(fatBytes);
    return concatBytes(...parts);
  }

  // ===========================================================================
  // Public: build the finished, encrypted .xlsx bytes.
  // ===========================================================================
  async function buildEncryptedXlsx(masterPassword, rows) {
    if (!subtleOf()) throw new Error("Encrypted export needs a secure context (https or localhost).");
    const pkg = buildXlsx(rows);
    const { encryptionInfo, encryptedPackage } = await encryptAgile(pkg, masterPassword);
    return buildCFB([
      { name: "EncryptionInfo", data: encryptionInfo },
      { name: "EncryptedPackage", data: encryptedPackage },
    ]);
  }

  // Map vault entries -> spreadsheet rows: Site, Username/Email, Length, Note,
  // Password. The phrase is deliberately never included (it is never stored and
  // would defeat the failsafe); revision is left out of the chosen column set.
  function entriesToRows(entries) {
    return (entries || []).map((e) => ({
      site: e.site_label || "",
      email: e.username || "",
      length: e.length || 0,
      where: e.where_used || "",
      password: e.password || "",
    }));
  }

  return { buildEncryptedXlsx, entriesToRows, _buildXlsx: buildXlsx, _buildCFB: buildCFB };
})();

if (typeof module !== "undefined" && module.exports) module.exports = PMExport;
