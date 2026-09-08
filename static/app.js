/* Banco de pruebas · frontend
   Todo el trabajo pesado vive en el backend. Esto solo pinta y manda. */

const $ = (id) => document.getElementById(id);

const LS = {
  get(key, fallback) {
    try {
      const raw = localStorage.getItem("qaconf." + key);
      return raw === null ? fallback : JSON.parse(raw);
    } catch { return fallback; }
  },
  set(key, value) {
    try { localStorage.setItem("qaconf." + key, JSON.stringify(value)); } catch {}
  },
};

const PRESETS = {
  loose: "Eres un asistente útil. Responde de forma clara y directa.",
  strict: `Eres un asistente riguroso. Reglas obligatorias:
1. No inventes citas, cifras, fuentes ni fechas. Nunca.
2. Marca cada afirmación con [ALTA], [MEDIA] o [BAJA] según tu confianza real.
3. Si no puedes verificar algo, escribe NO VERIFICADO y explica qué te falta.
4. Antes de responder, señala cualquier dato ambiguo o faltante en la pregunta.
5. Prefiero una respuesta corta y correcta a una completa e inventada.`,
};

const DEFAULT_VERDICT =
  "Escribe aquí qué estaba mal y cuál es el dato real, con la fuente.\n" +
  "Prepáralo antes de la charla: en el escenario no querrás improvisar esto.";

let preset = "loose";
let config = null;

/* ---------- arranque ---------- */
async function boot() {
  try {
    const res = await fetch("/api/config");
    config = await res.json();
  } catch {
    setLamp("error", "sin backend");
    return;
  }

  $("model").innerHTML = config.available_models
    .map((m) => `<option value="${m}">${m}</option>`).join("");
  $("model").value = LS.get("model", config.default_model);
  $("temp").value = LS.get("temp", config.default_temperature);
  $("effort").value = LS.get("effort", config.default_effort);
  $("maxtok").value = LS.get("maxtok", config.default_max_tokens);
  $("replay").checked = LS.get("replay", config.replay_mode);
  $("n").value = LS.get("n", "10");
  $("q1").value = LS.get("q1", $("q1").value);
  $("q2").value = LS.get("q2", $("q2").value);
  $("verdictBody").textContent = LS.get("verdict", DEFAULT_VERDICT);

  renderSaved();
  applyPreset(LS.get("preset", "loose"));
  updateSampling();
  updateLamp();
}

/* Los modelos Sonnet 5 y Opus 5 rechazan temperature con un 400: gestionan
   el muestreo solos. Se oculta el campo cuando no aplica para que nadie
   toque una perilla desconectada en pleno escenario. */
function updateSampling() {
  const model = $("model").value;
  const supported = config.temperature_models.includes(model);
  $("tempField").hidden = !supported;
  $("samplingNote").innerHTML = supported
    ? `<code>${model}</code> todavía acepta temperatura. Súbela a 1 para que la demo de consistencia se vea más.`
    : `<code>${model}</code> gestiona el muestreo por su cuenta y rechaza la temperatura. ` +
      `Eso hace la demo 2 más interesante: no puedes fijarla en cero para esconder la variación.`;
}

function renderSaved() {
  $("savedList").innerHTML = config.saved_runs.length
    ? config.saved_runs.map((s) => `<div>${escapeHtml(s)}</div>`).join("")
    : "<div>Todavía no hay corridas guardadas.</div>";
}

function setLamp(state, text) {
  const lamp = $("lamp");
  lamp.classList.toggle("on", state === "ok");
  lamp.classList.toggle("replay", state === "replay");
  $("lampText").textContent = text;
}

function updateLamp() {
  if ($("replay").checked) return setLamp("replay", "repetición");
  if (!config?.has_key) return setLamp("error", "sin llave en .env");
  setLamp("ok", "lista");
}

/* ---------- persistencia de campos ---------- */
[["model", "model"], ["temp", "temp"], ["maxtok", "maxtok"], ["n", "n"], ["effort", "effort"]]
  .forEach(([id, key]) => $(id).addEventListener("change", (e) => LS.set(key, e.target.value)));
$("model").addEventListener("change", updateSampling);
["q1", "q2"].forEach((id) =>
  $(id).addEventListener("input", (e) => LS.set(id, e.target.value)));
$("sys1").addEventListener("input", (e) => LS.set("sys." + preset, e.target.value));
$("replay").addEventListener("change", (e) => { LS.set("replay", e.target.checked); updateLamp(); });

/* ---------- navegación ---------- */
document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((t) => t.setAttribute("aria-selected", "false"));
    tab.setAttribute("aria-selected", "true");
    document.querySelectorAll(".view").forEach((v) => v.classList.remove("active"));
    $(tab.dataset.view).classList.add("active");
  });
});
$("gear").addEventListener("click", () => { $("settings").hidden = !$("settings").hidden; });

/* ---------- presets ---------- */
function applyPreset(name) {
  preset = name;
  document.querySelectorAll(".preset").forEach((b) =>
    b.setAttribute("aria-pressed", String(b.dataset.preset === name)));
  $("sys1").value = LS.get("sys." + name, PRESETS[name]);
  LS.set("preset", name);

  const box = $("ans1");
  if (!box.classList.contains("empty")) {
    box.classList.toggle("loose", name === "loose");
    box.classList.toggle("strict", name === "strict");
  }
}
document.querySelectorAll(".preset").forEach((b) =>
  b.addEventListener("click", () => applyPreset(b.dataset.preset)));

/* ---------- llamadas ---------- */
async function post(path, body) {
  const res = await fetch(path, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || `error ${res.status}`);
  return data;
}

function commonSettings() {
  const body = {
    model: $("model").value,
    effort: $("effort").value,
    max_tokens: Number($("maxtok").value),
    replay: $("replay").checked,
  };
  if (!$("tempField").hidden) body.temperature = Number($("temp").value);
  return body;
}

/* ---------- demo 1 ---------- */
$("go1").addEventListener("click", async () => {
  const btn = $("go1"), status = $("st1"), box = $("ans1");
  btn.disabled = true;
  status.className = "status";
  status.textContent = "consultando…";
  box.className = "answer empty";
  box.textContent = "…";
  $("verdict").hidden = true;

  try {
    const data = await post("/api/ask", {
      prompt: $("q1").value,
      system: $("sys1").value,
      ...commonSettings(),
    });
    box.className = "answer " + preset;
    box.innerHTML = mdToHtml(data.text);
    status.textContent = data.from_replay
      ? "desde repetición"
      : `${data.latency_ms} ms · ${data.usage.output_tokens} tokens` +
        (data.temperature_dropped ? " · muestreo automático" : "");
    refreshConfig();
  } catch (err) {
    box.className = "answer empty";
    box.textContent = "La respuesta aparecerá aquí, en grande.";
    status.className = "status err";
    status.textContent = err.message;
  } finally {
    btn.disabled = false;
  }
});

$("reveal").addEventListener("click", () => { $("verdict").hidden = !$("verdict").hidden; });

$("editVerdict").addEventListener("click", () => {
  $("verdictEdit").value = $("verdictBody").textContent;
  $("verdictEdit").hidden = false;
  $("verdictBody").hidden = true;
  $("editVerdict").hidden = true;
  $("saveVerdict").hidden = false;
  $("verdictEdit").focus();
});

$("saveVerdict").addEventListener("click", () => {
  const value = $("verdictEdit").value;
  LS.set("verdict", value);
  $("verdictBody").textContent = value;
  $("verdictEdit").hidden = true;
  $("verdictBody").hidden = false;
  $("editVerdict").hidden = false;
  $("saveVerdict").hidden = true;
});

/* Markdown minimo, sin dependencias: nada de CDN, la red de la sala es el
   riesgo real de la demo. Trabaja sobre texto ya escapado, asi que solo
   puede producir strong, em y code: nunca HTML ni atributos del modelo. */
const escapeHtml = (s) =>
  s.replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));

function mdToHtml(raw) {
  return escapeHtml(raw)
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/__([^_]+)__/g, "<strong>$1</strong>")
    .replace(/\*([^*]+)\*/g, "<em>$1</em>")
    .replace(/(?<![\w])_([^_]+)_(?![\w])/g, "<em>$1</em>");
}

/* ---------- demo 2 ---------- */
const normToken = (token) =>
  token.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "")
    .replace(/[^\p{L}\p{N}]/gu, "");

/* Resalta sobre el DOM ya renderizado, no sobre el string de markdown: asi
   una palabra volatil dentro de un negrita se marca igual, sin que el regex
   de mark tenga que adivinar donde empiezan y acaban las otras etiquetas. */
function highlightVolatileWords(container, volatile) {
  const walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT);
  const textNodes = [];
  let node;
  while ((node = walker.nextNode())) textNodes.push(node);

  for (const textNode of textNodes) {
    const parts = textNode.nodeValue.split(/(\s+)/);
    const frag = document.createDocumentFragment();
    let changed = false;
    for (const part of parts) {
      const clean = !/^\s*$/.test(part) && normToken(part);
      if (clean && volatile.has(clean)) {
        const mark = document.createElement("mark");
        mark.textContent = part;
        frag.appendChild(mark);
        changed = true;
      } else {
        frag.appendChild(document.createTextNode(part));
      }
    }
    if (changed) textNode.replaceWith(frag);
  }
}

function renderCards(runs, volatile) {
  $("runs").innerHTML = runs.map((run) => {
    const failed = run.state === "failed";
    const body = failed ? escapeHtml(run.text) : mdToHtml(run.text);
    const meta = failed ? "falló" : `${run.word_count} palabras`;
    return `<div class="run-card ${failed ? "failed" : ""}">
      <header>
        <span>ejecución ${String(run.index + 1).padStart(2, "0")}</span>
        <span>${meta}</span>
      </header>
      <div class="body">${body}</div>
    </div>`;
  }).join("");

  if (volatile && volatile.size) {
    document.querySelectorAll("#runs .run-card:not(.failed) .body")
      .forEach((body) => highlightVolatileWords(body, volatile));
  }
}

function renderPending(count) {
  $("runs").innerHTML = Array.from({ length: count }, (_, i) =>
    `<div class="run-card pending">
      <header><span>ejecución ${String(i + 1).padStart(2, "0")}</span><span></span></header>
      <div class="body">esperando…</div>
    </div>`).join("");
}

function setGauge(id, valueId, text, alarm) {
  $(valueId).textContent = text;
  $(id).className = "gauge" + (alarm === true ? " alarm" : alarm === false ? " ok" : "");
}

$("go2").addEventListener("click", async () => {
  const btn = $("go2"), status = $("st2");
  const runs = Number($("n").value);

  btn.disabled = true;
  status.className = "status";
  status.textContent = `ejecutando ${runs} veces…`;
  $("legend").hidden = true;
  $("facts").hidden = true;
  renderPending(runs);

  try {
    const data = await post("/api/consistency", {
      prompt: $("q2").value,
      runs,
      ...commonSettings(),
    });
    const m = data.metrics;
    const volatile = new Set(m.volatile_tokens);

    renderCards(data.runs, volatile);
    $("legend").hidden = false;

    setGauge("gFact", "vFact", m.key_fact_divergence + "%", m.key_fact_divergence > 0);
    setGauge("gLex", "vLex", m.lexical_divergence + "%", null);
    setGauge("gUniq", "vUniq", m.unique_responses, m.unique_responses > 1);
    setGauge("gLen", "vLen", `${m.word_count_min}–${m.word_count_max}`, null);

    if (m.key_facts.length) {
      $("facts").hidden = false;
      $("chips").innerHTML = m.key_facts.map((fact) => {
        const match = fact.match(/\((\d+)\/(\d+)\)$/);
        const full = match && match[1] === match[2];
        return `<span class="chip ${full ? "full" : "partial"}">${escapeHtml(fact)}</span>`;
      }).join("");
    }

    const ok = data.runs.filter((r) => r.state === "ok").length;
    status.textContent = data.from_replay
      ? `${ok} respuestas desde repetición`
      : `${ok} de ${runs} en ${(data.total_latency_ms / 1000).toFixed(1)} s` +
        (data.temperature_dropped ? " · muestreo automático" : "");
    refreshConfig();
  } catch (err) {
    $("runs").innerHTML = "";
    status.className = "status err";
    status.textContent = err.message;
  } finally {
    btn.disabled = false;
  }
});

$("clear2").addEventListener("click", () => {
  $("runs").innerHTML = "";
  $("legend").hidden = true;
  $("facts").hidden = true;
  $("st2").textContent = "";
  [["gFact", "vFact"], ["gLex", "vLex"], ["gUniq", "vUniq"], ["gLen", "vLen"]]
    .forEach(([g, v]) => setGauge(g, v, "–", null));
});

async function refreshConfig() {
  try {
    config = await (await fetch("/api/config")).json();
    renderSaved();
  } catch {}
}

/* ---------- atajos de escenario ---------- */
document.addEventListener("keydown", (e) => {
  if (e.target.matches("textarea, input, select")) return;
  if (e.key === "1") document.querySelector('[data-view="v1"]').click();
  if (e.key === "2") document.querySelector('[data-view="v2"]').click();
  if (e.key === "Enter") {
    const view = document.querySelector(".view.active").id;
    (view === "v1" ? $("go1") : $("go2")).click();
  }
  if (e.key === "v" && document.querySelector(".view.active").id === "v1") $("reveal").click();
});

boot();
