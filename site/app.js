import * as pdfjsLib from "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.10.38/pdf.min.mjs";

pdfjsLib.GlobalWorkerOptions.workerSrc =
  "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.10.38/pdf.worker.min.mjs";

const pdfInput = document.querySelector("#pdf-file");
const texInput = document.querySelector("#tex-file");
const pdfName = document.querySelector("#pdf-name");
const texName = document.querySelector("#tex-name");
const uploadStatus = document.querySelector("#upload-status");
const workspace = document.querySelector("#workspace");
const viewer = document.querySelector("#viewer");
const pdfStatus = document.querySelector("#pdf-status");
const selected = document.querySelector("#selected");
const replacement = document.querySelector("#replacement");
const findButton = document.querySelector("#find");
const matchSelect = document.querySelector("#match-select");
const applyButton = document.querySelector("#apply");
const downloadButton = document.querySelector("#download-tex");
const results = document.querySelector("#results");

let sourceText = "";
let sourceName = "paper.tex";
let pdfBytes = null;
let matches = [];

function normalize(value) {
  return value.replace(/\s+/g, " ").trim();
}

function sourceMatches(query) {
  const selectedText = normalize(query);
  if (!selectedText) return [];
  const lines = sourceText.split(/\n/);
  const exact = [];
  const normalized = [];
  const substring = [];
  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index];
    const clean = line.trim();
    const item = {
      file: sourceName,
      startLine: index + 1,
      endLine: index + 1,
      sourceText: line,
      selectedText,
      confidence: "substring",
    };
    if (line.includes(query)) exact.push({ ...item, confidence: "exact", selectedText: query });
    else if (normalize(line).includes(selectedText)) normalized.push({ ...item, confidence: "normalized" });
    else if (clean.includes(selectedText)) substring.push(item);
  }
  return exact.length ? exact : normalized.length ? normalized : substring;
}

function updateButtons() {
  const ready = matches.length > 0 && replacement.value.trim().length > 0;
  applyButton.disabled = !ready;
  downloadButton.disabled = !sourceText;
}

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
    span.title = item.fontName ? `PDF font resource: ${item.fontName}` : "PDF text span";
    layer.appendChild(span);
  }
  container.appendChild(layer);
}

async function renderPdf() {
  viewer.replaceChildren();
  const pdf = await pdfjsLib.getDocument({ data: pdfBytes }).promise;
  pdfStatus.textContent = `${pdf.numPages} 页已加载`;
  for (let pageNumber = 1; pageNumber <= pdf.numPages; pageNumber += 1) {
    const page = await pdf.getPage(pageNumber);
    const viewport = page.getViewport({ scale: 1.35 });
    const wrapper = document.createElement("div");
    wrapper.className = "page";
    wrapper.dataset.page = String(pageNumber);
    const canvas = document.createElement("canvas");
    canvas.width = viewport.width;
    canvas.height = viewport.height;
    wrapper.appendChild(canvas);
    await page.render({ canvasContext: canvas.getContext("2d"), viewport }).promise;
    renderTextLayer(wrapper, await page.getTextContent(), viewport);
    viewer.appendChild(wrapper);
  }
}

function showSelection() {
  const text = window.getSelection()?.toString().trim() || "";
  if (!text) return;
  selected.value = text;
  results.textContent = "已选中文字。点击“查找源代码位置”。";
  findButton.disabled = false;
  updateButtons();
}

async function loadFiles() {
  if (!pdfInput.files[0] || !texInput.files[0]) return;
  try {
    const pdfFile = pdfInput.files[0];
    const texFile = texInput.files[0];
    pdfBytes = new Uint8Array(await pdfFile.arrayBuffer());
    sourceText = await texFile.text();
    sourceName = texFile.name;
    pdfName.textContent = pdfFile.name;
    texName.textContent = texFile.name;
    uploadStatus.textContent = "PDF 和 TEX 已在浏览器中载入，可以开始选字。";
    workspace.classList.remove("locked");
    workspace.setAttribute("aria-disabled", "false");
    await renderPdf();
    updateButtons();
  } catch (error) {
    uploadStatus.textContent = `载入失败：${error.message}`;
  }
}

function findSource() {
  matches = sourceMatches(selected.value);
  matchSelect.replaceChildren();
  matches.forEach((match, index) => {
    const option = document.createElement("option");
    option.value = String(index);
    option.textContent = `${match.file}:${match.startLine} (${match.confidence})`;
    matchSelect.appendChild(option);
  });
  matchSelect.disabled = !matches.length;
  if (!matches.length) results.textContent = "没有找到源代码候选。请缩短选区，或确认上传的是对应 TEX。";
  else results.textContent = matches.map((item, index) => `${index + 1}. ${item.file}:${item.startLine} (${item.confidence})\n   ${item.sourceText}`).join("\n");
  updateButtons();
}

function applyMatch() {
  const match = matches[Number(matchSelect.value)];
  if (!match) return;
  const replacementText = replacement.value.replace(/\r\n/g, "\n");
  const lines = sourceText.split(/\n/);
  const line = lines[match.startLine - 1];
  const selectedText = match.selectedText || selected.value;
  lines[match.startLine - 1] = line.includes(selectedText)
    ? line.replace(selectedText, replacementText)
    : replacementText;
  sourceText = lines.join("\n");
  results.textContent = `已修改 ${match.file}:${match.startLine}\n请下载 TEX，或在本地桥接器中重新编译 PDF。`;
  downloadButton.disabled = false;
}

function downloadTex() {
  const blob = new Blob([sourceText], { type: "text/plain;charset=utf-8" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = sourceName;
  link.click();
  URL.revokeObjectURL(link.href);
}

document.addEventListener("mouseup", showSelection);
pdfInput.addEventListener("change", loadFiles);
texInput.addEventListener("change", loadFiles);
findButton.addEventListener("click", findSource);
replacement.addEventListener("input", updateButtons);
applyButton.addEventListener("click", applyMatch);
downloadButton.addEventListener("click", downloadTex);
