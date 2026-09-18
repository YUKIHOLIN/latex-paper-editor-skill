import * as pdfjsLib from "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.10.38/pdf.min.mjs";

pdfjsLib.GlobalWorkerOptions.workerSrc =
  "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.10.38/pdf.worker.min.mjs";

const viewer = document.querySelector("#viewer");
const status = document.querySelector("#status");
const selected = document.querySelector("#selected");
const replacement = document.querySelector("#replacement");
const results = document.querySelector("#results");
const findButton = document.querySelector("#find");
const matchSelect = document.querySelector("#match-select");
const applyButton = document.querySelector("#apply");
const publish = document.querySelector("#publish");
let lastMatches = [];

function showSelection() {
  const text = window.getSelection()?.toString().trim() || "";
  if (text) selected.value = text;
}

document.addEventListener("mouseup", showSelection);

function renderTextLayer(container, textContent, viewport) {
  const layer = document.createElement("div");
  layer.className = "text-layer";
  layer.style.width = `${viewport.width}px`;
  layer.style.height = `${viewport.height}px`;
  for (const item of textContent.items) {
    const span = document.createElement("span");
    const tx = pdfjsLib.Util.transform(viewport.transform, item.transform);
    const fontHeight = Math.max(6, Math.hypot(tx[2], tx[3]));
    span.textContent = item.str;
    span.style.left = `${tx[4]}px`;
    span.style.top = `${tx[5] - fontHeight}px`;
    span.style.fontSize = `${fontHeight}px`;
    span.style.transform = `scaleX(${Math.max(0.1, tx[0] / fontHeight)})`;
    layer.appendChild(span);
  }
  container.appendChild(layer);
}

async function renderPdf() {
  try {
    status.textContent = "Loading updated preview…";
    const pdf = await pdfjsLib.getDocument(`/build/paper.pdf?ts=${Date.now()}`).promise;
    status.textContent = `${pdf.numPages} page${pdf.numPages === 1 ? "" : "s"} loaded · updated ${new Date().toLocaleTimeString()}`;
    for (let pageNumber = 1; pageNumber <= pdf.numPages; pageNumber += 1) {
      const page = await pdf.getPage(pageNumber);
      const viewport = page.getViewport({ scale: 1.4 });
      const wrapper = document.createElement("div");
      wrapper.className = "page";
      wrapper.dataset.page = String(pageNumber);
      const canvas = document.createElement("canvas");
      canvas.width = viewport.width;
      canvas.height = viewport.height;
      wrapper.appendChild(canvas);
      const context = canvas.getContext("2d");
      await page.render({ canvasContext: context, viewport }).promise;
      renderTextLayer(wrapper, await page.getTextContent(), viewport);
      viewer.appendChild(wrapper);
    }
  } catch (error) {
    status.textContent = "PDF.js could not load; use Open PDF directly or check network access.";
    viewer.innerHTML = `<p class="error">${error.message}</p>`;
  }
}

async function findSource() {
  const response = await fetch("/api/preview", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ selectedText: selected.value, replacementText: replacement.value }),
  });
  const data = await response.json();
  lastMatches = data.matches || [];
  matchSelect.innerHTML = "";
  lastMatches.forEach((match, index) => {
    const option = document.createElement("option");
    option.value = String(index);
    option.textContent = `${match.file}:${match.startLine}-${match.endLine} (${match.confidence})`;
    matchSelect.appendChild(option);
  });
  matchSelect.disabled = lastMatches.length === 0;
  applyButton.disabled = lastMatches.length === 0 || !replacement.value.trim();
  if (!lastMatches.length) {
    results.textContent = "No source match. Try a shorter selection or identify the .tex file in your Codex request.";
    return;
  }
  results.textContent = lastMatches
    .map((match, index) => `${index + 1}. ${match.file}:${match.startLine}-${match.endLine} (${match.confidence})\n   ${match.sourceText}`)
    .join("\n");
}

async function applyAnnotation() {
  const match = lastMatches[Number(matchSelect.value)];
  applyButton.disabled = true;
  status.textContent = "Applying annotation and rebuilding preview…";
  results.textContent = "Applying source edit…";
  try {
    const response = await fetch("/api/apply", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ match, replacementText: replacement.value, publish: publish.checked }),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Annotation could not be applied.");
    }
    if (data.preview.status !== "ok") {
      throw new Error(`Source changed, but preview compilation failed:\n${data.preview.output || "check the compiler log"}`);
    }
    results.textContent = `Applied to ${data.applied.file}:${data.applied.startLine}-${data.applied.endLine}\nPreview rebuilt: ${data.preview.status}\nPublish: ${data.publish.status}${data.publish.message ? ` (${data.publish.message})` : ""}`;
    viewer.replaceChildren();
    await renderPdf();
  } finally {
    applyButton.disabled = lastMatches.length === 0 || !replacement.value.trim();
  }
}

findButton.addEventListener("click", () => findSource().catch((error) => { results.textContent = error.message; }));
replacement.addEventListener("input", () => { applyButton.disabled = lastMatches.length === 0 || !replacement.value.trim(); });
applyButton.addEventListener("click", () => applyAnnotation().catch((error) => { results.textContent = error.message; }));

renderPdf();
