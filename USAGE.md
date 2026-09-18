# LaTeX Paper Editor 使用说明

这个仓库提供一个可加载到 AI Agent 的 LaTeX 论文编辑技能，并附带 PDF 预览、PDF 文字选区匹配和字体诊断工具。

## 安装

```bash
git clone https://github.com/YUKIHOLIN/latex-paper-editor-skill.git
cd latex-paper-editor-skill
python3 install.py --target ~/.codex/skills
```

仓库是唯一的技能分发地址：

<https://github.com/YUKIHOLIN/latex-paper-editor-skill>

如果只是想立即试用，不安装本地环境也可以打开公网工作区：

<https://latex-paper-editor.netlify.app>

上传 PDF 和对应的 `.tex` 后，即可在 PDF 中选择文字、输入替换内容、选择源代码候选并下载更新后的 TEX。公网工作区在浏览器本地处理文件；需要自动重新编译 PDF 时，再克隆仓库并启动本地桥接服务。

将 `~/.codex/skills` 替换为目标 Agent 的技能目录即可。没有技能目录的 Agent，可以把 `skills/latex-paper-editor/SKILL.md` 作为项目指令或系统提示，并保留整个仓库供 Agent 执行脚本。

## 支持的软件和平台

### AI Agent

支持两种使用方式：

1. Agent 支持技能目录：安装 `latex-paper-editor` 技能。
2. Agent 不支持技能目录：加载 `skills/latex-paper-editor/SKILL.md`，并在仓库根目录执行命令。

适用对象包括：

- Codex
- Cursor
- Hermes
- DeepSeek Agent / Harness
- Doubao
- Kimi
- 其他能够读取 Markdown 指令并执行本地命令的 Agent

平台是否能使用完整功能，取决于它是否允许访问本地文件、运行 Python 3、运行 LaTeX，以及启动本地 HTTP 服务。只支持云端文本对话的平台仍可以读取技能说明，但可能无法使用本地 PDF 选区桥接。

### 编译软件

预览脚本支持：

- TeX Live
- MiKTeX（通过 `xelatex`、`pdflatex` 或兼容命令）
- MacTeX
- Tectonic（适合简单项目）

建议安装完整 TeX Live、MiKTeX 或 MacTeX，并确保 `xelatex` 在 PATH 中。包含中文、日文或韩文时优先使用 XeLaTeX。

## 创建或接入论文

将论文源文件放入仓库或你的论文项目目录。默认入口文件是 `paper.tex`；也可以使用包含 `\\documentclass` 的其他 `.tex` 文件。

预览编译：

```bash
python3 scripts/preview.py
```

生成文件位于 `build/paper.pdf`。编译失败时，脚本会保留上一次成功的 PDF。
预览脚本调用仓库内的 `scripts/compile_latex.py`，优先使用 `latexmk`，否则直接调用 `xelatex`、`pdflatex` 或 `lualatex`；不会依赖 Codex 安装目录中的脚本。

启动 PDF 选区桥接：

```bash
python3 scripts/start_bridge.py
```

然后打开：

```text
http://127.0.0.1:8765/
```

在 PDF 中选中文字，输入替换内容，点击 **Find source location**，选择源代码候选，然后点击 **Apply annotation**。桥接器会直接修改 `.tex`、重新编译 PDF，并立即刷新页面。**Also commit and push to GitHub** 默认不勾选；只有明确需要发布时才勾选。

## Netlify 公网版本

仓库中的 `site/` 是可部署到 Netlify 的静态网站。用户打开网站后先上传 PDF 和对应的 `.tex`，然后才能使用 PDF 选区、源代码候选、浏览器内修改和下载更新后的 TEX。文件只在用户浏览器中处理，不会上传到 Netlify。

在 Netlify 控制台新建站点时，将发布目录设置为 `site`；或者在仓库根目录运行：

```bash
npx netlify-cli deploy --dir=site --prod
```

公网版本不能在 Netlify 静态页面中执行 XeLaTeX，因此修改后不会直接生成新 PDF。需要即时重新编译时，在本地仓库运行 `python3 scripts/start_bridge.py`，再用下载的 TEX 编译预览。

### PDF 字体和 CID 诊断

安装可选依赖后：

```bash
python3 -m pip install -r requirements.txt
```

在 PDF 中选中文字后，右侧的诊断框会显示：

- 字体名称、BaseFont、字体家族、Type1/TrueType/Type0/CID 子类型和编码；
- 是否嵌入字体，以及在 `build/pdf-fonts/` 提取出的字体文件；
- 字号、RGB 颜色、透明度、粗体/斜体/等宽/衬线标志；
- PDF 页面坐标 bounding box、文字基线 origin 和 block/line/span 内容位置；
- PyMuPDF 根据 ToUnicode/CID 映射还原后的 Unicode 文本和映射状态。

也可以直接输出整页诊断：

```bash
python3 scripts/inspect_pdf.py build/paper.pdf --page 1
```

能力边界：PDF.js 负责渲染和选区；PyMuPDF 负责 PDF 字体、坐标和 ToUnicode 诊断；pdf-lib 适合浏览器端页面/对象操作但不适合可靠的 CID 字体写回。对于修改文字，推荐让桥接器更新 `.tex` 后由 XeLaTeX/xeCJK 重编译，这样中英文混排会重新执行合法的字体回退和 CID 编码。

## 中文和多语言字体

中文论文建议使用 XeLaTeX，并在导言区加入：

```tex
\documentclass{ctexart}
```

或者：

```tex
\usepackage{fontspec}
\usepackage{xeCJK}
\input{skills/latex-paper-editor/assets/cjk-font-fallback.tex}
```

字体诊断脚本会按顺序检查以下字体：

- Noto Serif/Sans CJK
- Source Han Serif/Sans
- Microsoft YaHei
- SimSun
- STSong
- WenQuanYi Zen Hei
- Droid Sans Fallback
- AR PL SungtiL GB

预览脚本发现非 ASCII 字符时会自动选择 XeLaTeX。若源文件没有 CJK 宏包，脚本会在 `\documentclass` 后自动加入仓库内的 `fontspec`、`xeCJK` 和字体回退模板；编译失败时会恢复原文件并保留上一次成功的 PDF。冷门 Unicode 字符仍需要系统安装包含对应字形的字体。

## Agent 使用示例

可以直接提出以下请求：

```text
修改引言第二段，使语气更正式，保留所有引用，然后重新编译 PDF。
```

```text
将 paper.tex 第 25 行的句子替换为：……，然后打开更新后的 PDF。
```

```text
检查论文中的中文字体配置，修复可能导致 PDF 乱码或空白的设置。
```

## 只有 PDF、没有 LaTeX 源码时

没有原始 `.tex` 文件时，不能可靠地进行源代码同步编辑。可以做文字提取和预览级 PDF 覆盖，但这不是可回溯的 LaTeX 修改。要实现稳定的“选中文字 → 修改源代码 → 重新生成 PDF”，请提供原始 LaTeX 工程。

## 常见问题

### PDF 中中文变成空白

确认使用 XeLaTeX，并加载 `ctex`、`xeCJK` 或 `fontspec`。然后检查本机是否安装 Noto CJK、思源字体、微软雅黑或宋体等中文字体。

### 选中文字找不到源代码

缩短选区，或者在源文件中给目标段落添加稳定标记：

```tex
% paper:id=discussion-paragraph
需要修改的段落。
% paper:end=discussion-paragraph
```

### 修改后 PDF 没有变化

先确认编译命令返回成功，再重新打开 `build/paper.pdf`。如果编译失败，脚本会保留旧 PDF，并在终端输出错误信息。
