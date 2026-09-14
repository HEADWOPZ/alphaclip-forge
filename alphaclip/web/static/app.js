const form = document.getElementById("forge-form");
const log = document.getElementById("log");
const result = document.getElementById("result");
const submit = document.getElementById("submit");

function addLog(text, cls) {
  const item = document.createElement("li");
  item.className = cls || "";
  item.textContent = text;
  if (log.querySelector(".idle")) log.innerHTML = "";
  log.appendChild(item);
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  result.hidden = true;
  result.innerHTML = "";
  log.innerHTML = "";
  addLog("Queuing forge job…");
  submit.disabled = true;

  const data = new FormData(form);
  data.set("mock", document.getElementById("mock").checked ? "true" : "false");
  data.set("rights", document.getElementById("rights").checked ? "true" : "false");

  try {
    addLog("Ingest → transcript → score → ffmpeg 9:16…");
    const response = await fetch("/api/forge", { method: "POST", body: data });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(payload.detail || response.statusText);
    }
    addLog(`Forged ${payload.clip_count} clip(s) · ${payload.preset}`, "ok");
    (payload.clips || []).forEach((clip) => {
      addLog(`${clip.filename} · ${clip.duration.toFixed(1)}s · ${clip.title}`, "ok");
    });
    result.hidden = false;
    const list = (payload.clips || [])
      .map((clip) => `<li><strong>${clip.title}</strong><br />${clip.hook}</li>`)
      .join("");
    result.innerHTML = `
      <a href="${payload.zip}">Download zip</a>
      <ul class="clip-list">${list}</ul>
    `;
  } catch (err) {
    addLog(err.message || String(err), "err");
  } finally {
    submit.disabled = false;
  }
});
