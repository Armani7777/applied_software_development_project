const $ = (id) => document.getElementById(id);

const title = $("title");
const draft = $("draft");
const saveHint = $("saveHint");
const messages = $("messages");
const hitsBox = $("hits");
const hitsEmpty = $("hitsEmpty");
let fileB64 = null;
let fileName = "";
let saveTimer = null;

function toast(text) {
  saveHint.textContent = text;
}

async function api(path, body) {
  const response = await fetch(path, {
    method: body === undefined ? "GET" : "POST",
    headers: body === undefined ? {} : { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "Запрос не прошёл");
  }
  return data;
}

function renderPapers(papers) {
  $("railPapers").innerHTML = papers.map((p) => (
    `<article class="rail-card"><b>${escapeHtml(p.title)}</b>${escapeHtml(p.authors)}, ${escapeHtml(p.year)} · ${p.page_count} стр.</article>`
  )).join("");
  $("libList").innerHTML = papers.map((p) => (
    `<article class="lib-item">
      <h3>${escapeHtml(p.title)}</h3>
      <p class="muted">${escapeHtml(p.authors)} · ${escapeHtml(p.year)} · ${p.page_count} стр., ${p.chars} знаков</p>
      <button class="kill" data-del="${p.id}" type="button">убрать</button>
    </article>`
  )).join("") || "<p class='muted'>Пока пусто.</p>";
  document.querySelectorAll("[data-del]").forEach((btn) => {
    btn.onclick = async () => {
      renderPapers((await api("/api/papers/remove", { id: btn.dataset.del })).papers);
    };
  });
}

function escapeHtml(value) {
  return String(value || "").replace(/[&<>"']/g, (ch) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[ch]));
}

function addMessage(role, text) {
  const div = document.createElement("div");
  div.className = "bubble " + role;
  div.textContent = text;
  messages.append(div);
  messages.scrollTop = messages.scrollHeight;
}

function showHits(hits) {
  if (!hits || !hits.length) {
    hitsEmpty.hidden = false;
    hitsBox.innerHTML = "";
    return;
  }
  hitsEmpty.hidden = true;
  hitsBox.innerHTML = hits.map((h) => `
    <article class="hit">
      <b>${escapeHtml(h.cite)}</b>
      <span class="stamp ${h.status}">${h.status} · с. ${h.page}</span>
      <div>${escapeHtml(h.title)}</div>
      <q>${escapeHtml(h.sentence)}</q>
    </article>
  `).join("");
}

function insertDraft(text) {
  if (!text) {
    return;
  }
  const start = draft.selectionStart;
  const before = draft.value.slice(0, start);
  const after = draft.value.slice(draft.selectionEnd);
  const pad = before && !before.endsWith("\n") ? "\n\n" : "";
  draft.value = before + pad + text + (after.startsWith("\n") ? "" : "\n") + after;
  scheduleSave();
}

function selection() {
  return draft.value.slice(draft.selectionStart, draft.selectionEnd).trim();
}

function scheduleSave() {
  toast("сохраняю…");
  clearTimeout(saveTimer);
  saveTimer = setTimeout(async () => {
    await api("/api/draft", { title: title.value, draft: draft.value });
    toast("сохранено");
  }, 500);
}

async function runAi(action, query) {
  toast("собираю из библиотеки…");
  const data = await api("/api/ai", {
    action,
    query,
    title: title.value,
    draft: draft.value,
  });
  showHits(data.hits);
  if (action === "chat") {
    addMessage("bot", data.text);
  } else if (action === "cite" && data.inline) {
    insertDraft(data.inline);
    addMessage("bot", data.text);
  } else {
    insertDraft(data.text);
    addMessage("bot", data.text);
  }
  if (data.bibliography && data.bibliography.length) {
    addMessage("bot", "Список: " + data.bibliography.join(" "));
  }
  toast("готово");
  if (action !== "chat") {
    document.querySelector('[data-tab="hits"]').click();
  }
}

title.addEventListener("input", scheduleSave);
draft.addEventListener("input", scheduleSave);

document.querySelectorAll(".nav").forEach((btn) => {
  btn.onclick = () => {
    document.querySelectorAll(".nav").forEach((b) => b.classList.toggle("on", b === btn));
    $("viewDoc").hidden = btn.dataset.view !== "doc";
    $("viewLib").hidden = btn.dataset.view !== "lib";
  };
});

document.querySelectorAll(".tab").forEach((btn) => {
  btn.onclick = () => {
    document.querySelectorAll(".tab").forEach((b) => b.classList.toggle("on", b === btn));
    $("tabChat").hidden = btn.dataset.tab !== "chat";
    $("tabHits").hidden = btn.dataset.tab !== "hits";
    $("tabCheck").hidden = btn.dataset.tab !== "check";
  };
});

document.querySelectorAll("[data-ai]").forEach((btn) => {
  btn.onclick = async () => {
    const action = btn.dataset.ai;
    const query = action === "paraphrase" || action === "cite" ? (selection() || draft.value.slice(-400)) : title.value;
    btn.disabled = true;
    try {
      await runAi(action, query);
    } catch (error) {
      addMessage("bot", error.message);
      toast(error.message);
    } finally {
      btn.disabled = false;
    }
  };
});

$("chatForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const q = $("question").value.trim();
  if (!q) {
    return;
  }
  addMessage("user", q);
  $("question").value = "";
  try {
    await runAi("chat", q);
    document.querySelector('[data-tab="chat"]').click();
  } catch (error) {
    addMessage("bot", error.message);
  }
});

$("openAdd").onclick = () => document.querySelector('[data-view="lib"]').click();

$("pFile").addEventListener("change", async (event) => {
  const file = event.target.files && event.target.files[0];
  fileB64 = null;
  fileName = "";
  $("pFileName").textContent = "";
  if (!file) {
    return;
  }
  const buffer = await file.arrayBuffer();
  const bytes = new Uint8Array(buffer);
  let binary = "";
  bytes.forEach((b) => { binary += String.fromCharCode(b); });
  fileB64 = btoa(binary);
  fileName = file.name;
  $("pFileName").textContent = file.name;
  if (!$("pTitle").value) {
    $("pTitle").value = file.name.replace(/\.(pdf|txt)$/i, "");
  }
});

$("addForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const state = (await api("/api/papers", {
      title: $("pTitle").value,
      authors: $("pAuthors").value,
      year: $("pYear").value,
      text: $("pText").value,
      file_b64: fileB64,
      filename: fileName,
    })).state;
    renderPapers(state.papers);
    $("addForm").reset();
    fileB64 = null;
    $("pFileName").textContent = "";
    toast("статья в библиотеке");
  } catch (error) {
    toast(error.message);
  }
});

$("doCheck").onclick = async () => {
  try {
    const data = await api("/api/check", {
      page: $("cPage").value,
      page_text: $("cPageText").value,
      quote: $("cQuote").value,
    });
    $("checkOut").textContent = `страница ${data.page} · ${data.status}`;
  } catch (error) {
    $("checkOut").textContent = error.message;
  }
};

addMessage("bot", "Я пишу только из статей слева. Спросите, например: «что они говорят про номер страницы у цитаты?» или нажмите «План главы».");

api("/api/state").then((state) => {
  title.value = state.title;
  draft.value = state.draft;
  renderPapers(state.papers);
}).catch((error) => toast(error.message));
