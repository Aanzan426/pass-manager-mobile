/*
 * app.js — UI controller for the mobile app.
 * ==========================================
 * Same interface and behaviour as the desktop, but everything runs IN THE PHONE:
 * generation is PMCrypto, storage is PMStore (encrypted localStorage). No server,
 * no network. Works fully offline once installed.
 */
"use strict";

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => Array.from(document.querySelectorAll(sel));

// ---------- screen routing ----------
const SCREENS = ["screen-setup", "screen-unlock", "screen-app", "screen-manual"];
let _returnScreen = "screen-app"; // where "Back" from the manual returns to
function show(screenId) {
  SCREENS.forEach((id) => { $("#" + id).hidden = (id !== screenId); });
  window.scrollTo(0, 0);
}

function route() {
  if (!PMStore.isInitialised()) return show("screen-setup");
  if (!PMStore.isUnlocked()) return show("screen-unlock");
  show("screen-app");
  loadVault();
}

// ---------- toast ----------
let toastTimer = null;
function toast(msg) {
  const t = $("#toast");
  t.textContent = msg;
  t.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => (t.hidden = true), 2200);
}

function escapeHtml(s) {
  return (s || "").replace(/[&<>"']/g, (c) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
  ));
}

// ---------- setup (step 1 of 2: master password) ----------
let _pendingMaster = null; // held only between the master step and the export step
$("#setup-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const master = $("#setup-master").value;
  const confirm = $("#setup-confirm").value;
  const err = $("#setup-error");
  err.textContent = "";
  if (master.length < 6) { err.textContent = "Master password must be at least 6 characters."; return; }
  if (master !== confirm) { err.textContent = "The two master passwords do not match."; return; }
  if (!PMCrypto.hasSubtle()) {
    err.textContent = "This page needs a secure context (https or localhost) to encrypt your vault. See the manual.";
    return;
  }
  // Step 2: ask for the export password before actually creating the vault.
  _pendingMaster = master;
  openExportSetup("create");
});

// ---------- unlock ----------
$("#unlock-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const master = $("#unlock-master").value;
  const err = $("#unlock-error");
  err.textContent = "";
  try {
    const ok = await PMStore.unlock(master);
    if (!ok) { err.textContent = "Incorrect master password."; return; }
    $("#unlock-master").value = "";
    route();
  } catch (e2) { err.textContent = e2.message; }
});

// ---------- nav ----------
$("#nav-lock").addEventListener("click", (e) => { e.preventDefault(); PMStore.lock(); route(); });
$("#nav-manual").addEventListener("click", (e) => { e.preventDefault(); _returnScreen = "screen-app"; renderManual(); show("screen-manual"); });
$("#manual-back-top").addEventListener("click", (e) => { e.preventDefault(); show(_returnScreen); });
$("#setup-manual-link").addEventListener("click", (e) => { e.preventDefault(); _returnScreen = "screen-setup"; renderManual(); show("screen-manual"); });
$("#unlock-manual-link").addEventListener("click", (e) => { e.preventDefault(); _returnScreen = "screen-unlock"; renderManual(); show("screen-manual"); });

// ---------- generator ----------
const phraseEl = $("#phrase");
const siteEl = $("#site");
const usernameEl = $("#username");
const lengthEl = $("#length");
const lenVal = $("#len-val");
const whereEl = $("#where_used");
const genMsg = $("#gen-msg");

$("#show-phrase").addEventListener("change", (e) => { phraseEl.type = e.target.checked ? "text" : "password"; });
lengthEl.addEventListener("input", () => (lenVal.textContent = lengthEl.value));

function setGenMsg(text, ok = false) {
  genMsg.textContent = text;
  genMsg.className = "form-msg " + (ok ? "ok" : "error");
}
function clampLen(v) { return Math.max(8, Math.min(parseInt(v, 10) || 20, 64)); }

$("#btn-preview").addEventListener("click", async () => {
  setGenMsg("");
  const phrase = phraseEl.value.trim();
  const site = siteEl.value.trim();
  if (!phrase || !site) { setGenMsg("Phrase and site are required."); return; }
  try {
    const pw = await PMCrypto.derivePassword(phrase, site, 1, clampLen(lengthEl.value), PMStore.getIterations());
    $("#preview-box").hidden = false;
    $("#preview-pass").textContent = pw;
  } catch (e) { setGenMsg(e.message); }
});

$("#btn-save").addEventListener("click", async () => {
  setGenMsg("");
  const phrase = phraseEl.value.trim();
  const site = siteEl.value.trim();
  if (!phrase || !site) { setGenMsg("Both a memorised phrase and a site label are required."); return; }
  const length = clampLen(lengthEl.value);
  try {
    const password = await PMCrypto.derivePassword(phrase, site, 1, length, PMStore.getIterations());
    await PMStore.insertEntry({
      site_label: site, username: usernameEl.value, password,
      revision: 1, length, where_used: whereEl.value,
    });
    setGenMsg("Saved to vault.", true);
    $("#preview-box").hidden = false;
    $("#preview-pass").textContent = password;
    phraseEl.value = ""; siteEl.value = ""; usernameEl.value = ""; whereEl.value = "";
    loadVault();
    toast("Password generated & saved");
  } catch (e) { setGenMsg(e.message); }
});

// ---------- vault ----------
let ENTRIES = [];

function loadVault() {
  ENTRIES = PMStore.listEntries();
  renderVault();
}

function renderVault() {
  const term = ($("#search").value || "").toLowerCase();
  const list = $("#vault-list");
  const filtered = ENTRIES.filter((e) =>
    !term ||
    e.site_label.toLowerCase().includes(term) ||
    (e.username || "").toLowerCase().includes(term) ||
    (e.where_used || "").toLowerCase().includes(term)
  );

  if (filtered.length === 0) {
    list.innerHTML = `<div class="empty">${ENTRIES.length === 0
      ? "Your vault is empty. Generate your first password above."
      : "No entries match your search."}</div>`;
    return;
  }

  list.innerHTML = filtered.map((e) => {
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
            <div class="pass-val" data-pass="${escapeHtml(e.password)}" data-shown="0" title="Tap to reveal / hide">${masked}</div>
            <button class="icon-btn copy" title="Copy">Copy</button>
        </div>
        <div class="notes-label">Where used ${e.needs_update ? "· needs updating on the real site" : ""}</div>
        <textarea class="notes-box" rows="2" placeholder="Where did you use this password?">${escapeHtml(e.where_used)}</textarea>
        <div class="entry-actions">
            <button class="mini-btn rotate">↻ Rotate</button>
            ${e.needs_update ? `<button class="mini-btn confirm">✓ Mark updated</button>` : ""}
            <button class="mini-btn del">Delete</button>
        </div>
    </div>`;
  }).join("");

  wireEntries();
}

function wireEntries() {
  $$(".entry").forEach((card) => {
    const id = parseInt(card.dataset.id, 10);

    const passEl = card.querySelector(".pass-val");
    passEl.addEventListener("click", () => {
      const shown = passEl.dataset.shown === "1";
      if (shown) {
        passEl.textContent = "•".repeat(Math.min(passEl.dataset.pass.length, 24));
        passEl.dataset.shown = "0";
      } else {
        passEl.textContent = passEl.dataset.pass;
        passEl.dataset.shown = "1";
      }
    });

    card.querySelector(".copy").addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(passEl.dataset.pass);
        toast("Password copied");
      } catch {
        toast("Copy failed — reveal and copy manually");
      }
    });

    const notes = card.querySelector(".notes-box");
    notes.addEventListener("blur", async () => {
      const original = (ENTRIES.find((e) => e.id === id) || {}).where_used || "";
      if (notes.value === original) return;
      try {
        await PMStore.setWhereUsed(id, notes.value);
        const ent = ENTRIES.find((e) => e.id === id);
        if (ent) ent.where_used = notes.value;
        toast("Notes saved");
      } catch (e) { toast(e.message); }
    });

    card.querySelector(".rotate").addEventListener("click", () => openRotate(id));

    const confirmBtn = card.querySelector(".confirm");
    if (confirmBtn) {
      confirmBtn.addEventListener("click", async () => {
        try {
          await PMStore.setNeedsUpdate(id, false);
          toast("Marked as updated");
          loadVault();
        } catch (e) { toast(e.message); }
      });
    }

    card.querySelector(".del").addEventListener("click", async () => {
      if (!confirm("Delete this entry? You can still re-derive it from your phrase later.")) return;
      try {
        await PMStore.deleteEntry(id);
        toast("Entry deleted");
        loadVault();
      } catch (e) { toast(e.message); }
    });
  });
}

$("#search").addEventListener("input", renderVault);

// ---------- rotate modal ----------
let rotateId = null;
function openRotate(id) {
  rotateId = id;
  const ent = PMStore.getEntry(id);
  $("#rotate-target").textContent =
    `${ent.site_label}${ent.username ? " · " + ent.username : ""} (currently rev ${ent.revision})`;
  $("#rotate-phrase").value = "";
  $("#rotate-msg").textContent = "";
  $("#rotate-modal").hidden = false;
  $("#rotate-phrase").focus();
}
function closeRotate() { $("#rotate-modal").hidden = true; rotateId = null; }

$("#rotate-cancel").addEventListener("click", closeRotate);
$("#rotate-go").addEventListener("click", async () => {
  const phrase = $("#rotate-phrase").value.trim();
  const msg = $("#rotate-msg");
  if (!phrase) { msg.className = "form-msg error"; msg.textContent = "Enter your phrase."; return; }
  try {
    const ent = PMStore.getEntry(rotateId);
    const newRev = ent.revision + 1;
    const password = await PMCrypto.derivePassword(phrase, ent.site_label, newRev, ent.length, PMStore.getIterations());
    await PMStore.updateEntryPassword(rotateId, password, newRev);
    closeRotate();
    toast(`Rotated to rev ${newRev} — now update it on the real site`);
    loadVault();
  } catch (e) { msg.className = "form-msg error"; msg.textContent = e.message; }
});

// ---------- export password setup (the 2nd password) ----------
let _exportSetupMode = "create"; // "create" = first run, "set" = existing vault

function openExportSetup(mode) {
  _exportSetupMode = mode;
  $("#export-setup-pass").value = "";
  $("#export-setup-confirm").value = "";
  $("#export-setup-msg").textContent = "";
  if (mode === "create") {
    $("#export-setup-title").textContent = "Create your export password";
    $("#export-setup-note").textContent =
      "This second password will be required whenever you export your saved passwords to an " +
      "Excel (.xlsx) file. Keep it in your head — like your master password, it is never stored anywhere.";
    $("#export-setup-go").textContent = "Create vault →";
    $("#export-setup-cancel").textContent = "Back";
  } else {
    $("#export-setup-title").textContent = "Set your export password";
    $("#export-setup-note").textContent =
      "This vault was created before exporting existed. Set a second password now — it is required " +
      "whenever you export to Excel, and is never stored. We'll export right after.";
    $("#export-setup-go").textContent = "Save & export →";
    $("#export-setup-cancel").textContent = "Cancel";
  }
  $("#export-setup-modal").hidden = false;
  $("#export-setup-pass").focus();
}
function closeExportSetup() { $("#export-setup-modal").hidden = true; }

$("#export-setup-cancel").addEventListener("click", () => {
  closeExportSetup();
  _pendingMaster = null;
});

$("#export-setup-go").addEventListener("click", async () => {
  const pw = $("#export-setup-pass").value;
  const confirm = $("#export-setup-confirm").value;
  const msg = $("#export-setup-msg");
  msg.className = "form-msg error";
  if (pw.length < 6) { msg.textContent = "Export password must be at least 6 characters."; return; }
  if (pw !== confirm) { msg.textContent = "The two export passwords do not match."; return; }
  try {
    if (_exportSetupMode === "create") {
      await PMStore.createMaster(_pendingMaster, pw);
      _pendingMaster = null;
      closeExportSetup();
      toast("Vault created");
      route();
    } else {
      await PMStore.setExportPassword(pw);
      closeExportSetup();
      doExport();
    }
  } catch (e) { msg.textContent = e.message; }
});

// ---------- export (verify the 2nd password, then build the encrypted .xlsx) ----------
$("#nav-export").addEventListener("click", (e) => {
  e.preventDefault();
  if (!PMStore.isUnlocked()) { route(); return; }
  if ((PMStore.listEntries() || []).length === 0) { toast("Vault is empty — nothing to export"); return; }
  if (!PMCrypto.hasSubtle()) { toast("Export needs a secure context (https or localhost)"); return; }
  if (!PMStore.hasExportPassword()) { openExportSetup("set"); return; }
  openExportVerify();
});

function openExportVerify() {
  $("#export-verify-pass").value = "";
  $("#export-verify-msg").textContent = "";
  $("#export-verify-modal").hidden = false;
  $("#export-verify-pass").focus();
}
function closeExportVerify() { $("#export-verify-modal").hidden = true; }

$("#export-verify-cancel").addEventListener("click", closeExportVerify);
$("#export-verify-go").addEventListener("click", async () => {
  const pw = $("#export-verify-pass").value;
  const msg = $("#export-verify-msg");
  msg.className = "form-msg error";
  if (!pw) { msg.textContent = "Enter your export password."; return; }
  const ok = await PMStore.verifyExportPassword(pw);
  if (!ok) { msg.textContent = "Incorrect export password."; return; }
  closeExportVerify();
  doExport();
});

function exportFilename() {
  const d = new Date();
  const p = (n) => String(n).padStart(2, "0");
  return `vault-export-${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}.xlsx`;
}

async function doExport() {
  if (!PMCrypto.hasSubtle()) { toast("Export needs a secure context (https or localhost)"); return; }
  toast("Encrypting your backup… this can take a few seconds");
  // Let the toast paint before the synchronous, CPU-heavy key derivation runs.
  await new Promise((r) => setTimeout(r, 60));
  try {
    const rows = PMExport.entriesToRows(PMStore.listEntries());
    const bytes = await PMExport.buildEncryptedXlsx(PMStore.getMaster(), rows);
    const blob = new Blob([bytes], {
      type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = exportFilename();
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(() => URL.revokeObjectURL(url), 4000);
    toast("Exported — open it with your master password");
  } catch (e) { toast(e.message || "Export failed"); }
}

// ---------- manual ----------
function renderManual() {
  $("#manual-body").innerHTML = MANUAL_HTML;
}

// ---------- boot ----------
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("sw.js").catch(() => { /* offline-first still works on next loads */ });
  });
}
route();
