<!-- ============================================================ -->
<!-- HERO HEADER                                                   -->
<!-- ============================================================ -->

<div align="center">

<img src="https://raw.githubusercontent.com/yourname/yourrepo/main/.github/banner.svg" alt="Agentic Bootstrapper IDE" width="100%" style="max-width: 900px;">

<h1>⚡ Agentic Bootstrapper IDE</h1>

<p><strong>The 30-second way to start any Python project.</strong><br>
Double-click → pick a template → working project in VS Code.</p>

<p>
  <a href="#installation"><img src="https://img.shields.io/badge/⬇_Install-30_seconds-0e639c?style=for-the-badge" alt="Install"></a>
  <a href="#features"><img src="https://img.shields.io/badge/✨_Features-12_templates-4ec9b0?style=for-the-badge" alt="Features"></a>
  <a href="#ai-companion"><img src="https://img.shields.io/badge/🤖_AI-100%25_offline-16825d?style=for-the-badge" alt="AI"></a>
</p>

<p>
  <img src="https://img.shields.io/badge/Python-3.9+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/PyQt6-6.x-41CD52?style=flat-square&logo=qt&logoColor=white" alt="PyQt6">
  <img src="https://img.shields.io/badge/Platform-Windows_10%2F11-0078D6?style=flat-square&logo=windows&logoColor=white" alt="Windows">
  <img src="https://img.shields.io/badge/AI-Qwen2.5--Coder_1.5B-FF6B6B?style=flat-square" alt="AI">
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=flat-square" alt="License">
  <img src="https://img.shields.io/badge/Status-Stable-success?style=flat-square" alt="Status">
</p>

</div>

---

<!-- ============================================================ -->
<!-- WHAT IS THIS                                                  -->
<!-- ============================================================ -->

## 🤔 What is this?

**A tiny app that sets up Python projects for you.**

You know how every Python project starts the same boring way?

- Install Python ✅
- Open a terminal
- Type `python -m venv .venv`
- Type `.venv\Scripts\activate`
- Type `pip install -r requirements.txt`
- Wait
- Realize pip is outdated, upgrade it
- Wait again
- Finally open VS Code

**That's 10 minutes of typing before you've written a single line of code.**

This IDE does all of that in **one click**.

<br>

<div align="center">

### 🎯 The whole idea, in one image

<pre>
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│                     │    │                     │    │                     │
│  Double-click the   │───▶│  Pick a template    │───▶│  Working project    │
│     .exe file       │    │  (Flask? ML? CLI?)  │    │  in VS Code. Done.  │
│                     │    │                     │    │                     │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
       10 seconds               5 seconds                  15 seconds

                    ⏱️  TOTAL TIME: ~30 seconds
</pre>

</div>

---

<!-- ============================================================ -->
<!-- WHAT IT LOOKS LIKE                                            -->
<!-- ============================================================ -->

## 📸 What it looks like

<div align="center">

<pre>
┌──────────────────────────────────────────────────────────────────────────┐
│ flask_test        CPU 12%   RAM 42%   GPU: Integrated    [Setup] [Run]  │
├────────────────┬────────────────────────────────┬────────────────────────┤
│ EXPLORER       │ EDITOR                         │ AI COMPANION           │
│                │ ┌─ app.py ─┬─ main.py ─┐         │                        │
│ ▸ templates/   │ │ 1  from flask import...     │ │ You: what does this    │
│ ▸ static/      │ │ 2                            │ │      app do?           │
│   app.py       │ │ 3  app = Flask(__name__)     │ │                        │
│   requirements │ │ 4                            │ │ Qwen: This is a Flask  │
│                │ │ 5  @app.route("/")           │ │ notes app with three   │
│ [New File]     │ │ 6  def home():               │ │ endpoints...           │
│ [Refresh]      │ │ 7      return ...            │ │                        │
│                │ │                              │ │ 📎 📁 [Ask...]  [Send] │
├────────────────┴────────────────────────────────┴────────────────────────┤
│ TERMINAL · Ctrl+C to interrupt                                          │
│ [venv] ready: ...\.venv\Scripts\python.exe                              │
│ [pip] Successfully installed flask-3.1.3 Jinja2-3.1.6 ...               │
│  * Running on http://127.0.0.1:5000                                     │
└──────────────────────────────────────────────────────────────────────────┘
</pre>

</div>

---

<!-- ============================================================ -->
<!-- FEATURES AT A GLANCE                                          -->
<!-- ============================================================ -->

## ✨ Features

<div align="center">

| | |
|:---:|:---|
| **📦 12 templates** | Flask, FastAPI, Django, ML, scraping, GUI, CLI, tests, and more — one click each |
| **🐍 Auto Python setup** | Creates the virtual environment for you. No terminal. No activation scripts. |
| **📥 Auto pip install** | Reads `requirements.txt` and installs everything. pip is bundled — no download needed. |
| **🤖 Local AI assistant** | Qwen2.5-Coder 1.5B running on your CPU. Zero internet. Zero API keys. Zero cost. |
| **⚠️ ML hardware guardrail** | Warns you before running torch/tensorflow code that will melt your laptop. |
| **📊 Live hardware HUD** | CPU % and RAM % in the title bar. See when your script is hogging the machine. |
| **⌨️ Ctrl+C that works** | Interrupt scripts like a real terminal. Kills the whole process tree. |
| **🎨 VS Code theme** | Looks familiar. Dark. Legible. No eye strain. |
| **🚀 Open in VS Code** | One button. Hands off the finished workspace. Use real tools for real work. |
| **💾 Single file** | One `ai_ide.py`. No setup scripts. No config files. Just run it. |

</div>

---

<!-- ============================================================ -->
<!-- INSTALLATION                                                  -->
<!-- ============================================================ -->

## 🚀 Installation

### ⚠️ Read this first

You only need to install **Python once**. Everything else is automatic.

<br>

### Step 1 — Install Python (if you don't have it)

1. Go to **<https://python.org/downloads>**
2. Click the big yellow **"Download Python 3.x.x"** button
3. Run the installer
4. **⚠️ IMPORTANT:** tick the box that says **"Add Python to PATH"** at the bottom of the first screen
5. Click **"Install Now"**
6. Wait for it to finish

**Not sure if you already have Python?** Open PowerShell (press <kbd>Win</kbd>+<kbd>R</kbd>, type `powershell`, press Enter) and run:

```powershell
python --version
```

If you see `Python 3.9` or higher → you're good, skip to Step 2.

If you see an error → do the install above.

<br>

### Step 2 — Download this project

Click the green **"Code"** button at the top of this page → **"Download ZIP"** → extract it anywhere you like.

<br>

### Step 3 — Get the AI model (~1 GB)

The IDE uses a local AI model. It's too big for GitHub (they have a 100 MB file limit), so you download it separately.

1. Search Hugging Face for: **`Qwen2.5-Coder-1.5B-Instruct-GGUF`**
2. Download the file ending in **`-Q4_K_M.gguf`** (~1 GB)
3. Rename it to exactly: `qwen2.5-coder-1.5b-instruct-q4_k_m.gguf`
4. Put it inside the `model` folder in your extracted project

Your folder should look like this:

```
your-project-folder/
├── ai_ide.py
├── build.bat
├── README.md
└── model/
    └── qwen2.5-coder-1.5b-instruct-q4_k_m.gguf    ← 1 GB file here
```

<br>

### Step 4 — Build the exe

1. Double-click **`build.bat`**
2. A black window opens. It says **"Building exe (3-6 min)"**
3. **Don't touch it. Don't close it.** Let it run
4. When it says **"BUILD COMPLETE"** → press any key to close

**That's it.** The exe is ready.

> 💡 **What did build.bat do?** It installed PyQt6, psutil, llama-cpp-python, and PyInstaller into your Python, then packaged everything into a standalone `.exe` file. You don't need to understand it — it just works.

<br>

### Step 5 — Launch

Go to `dist\ai_ide\` and double-click **`ai_ide.exe`**.

You'll see:
1. A splash screen ("Initializing AI Workspace")
2. Model loads (10-20 seconds)
3. A project picker appears

**That's the IDE.** Pick a template. You're done.

<br>

### 🎉 First time? Try this:

1. **Project name:** `hello_test`
2. **Template:** `Flask Web App`
3. Click **Create Project**
4. Wait ~30 seconds (installs Flask automatically)
5. Press <kbd>F5</kbd>
6. Open <http://127.0.0.1:5000> in your browser

You just built a working web app. **No terminal. No pip. No venv commands. Nothing.**

---

<!-- ============================================================ -->
<!-- TEMPLATES                                                     -->
<!-- ============================================================ -->

## 📦 All 12 templates

<div align="center">

| Icon | Template | What it gives you |
|:---:|:---|:---|
| 📄 | **Empty Project** | Just a folder. Scaffold it yourself |
| 🐍 | **Python Script** | `main.py` that prints hello. Quick tests |
| ⌨️ | **CLI Tool** | Working command-line app with `--name` and `--count` args |
| 🌶️ | **Flask Web App** | Notes API with `/`, `/api/notes`, `/health` + dark HTML page |
| ⚡ | **FastAPI Web API** | Typed API with auto-Swagger docs at `/docs` |
| 🎸 | **Django Web App** | Minimal Django with one JSON endpoint |
| 📊 | **Data Science** | pandas demo showing shape, head, describe, group-by |
| 🤖 | **ML Starter** | sklearn regression + a `guardrail_demo.py` to test warnings |
| 🕷️ | **Web Scraper** | requests + BeautifulSoup demo |
| 🖼️ | **Tkinter GUI** | Small desktop app with input + button |
| 📚 | **Package** | Installable Python package with `pyproject.toml` |
| 🧪 | **Pytest Suite** | 5 working tests including parametrized cases |

</div>

---

<!-- ============================================================ -->
<!-- AI COMPANION                                                  -->
<!-- ============================================================ -->

## 🤖 AI companion

Your own coding assistant. Runs on your machine. Never leaves your machine.

<br>

### What it's good at

<div align="center">

| ✅ Ask it | Example |
|:---|:---|
| **Explain code** | *"Explain this function"* — highlight code, click 📎, send |
| **Refactor** | *"Rewrite this to use a list comprehension"* |
| **Debug** | *"This returns None, why?"* — paste the traceback |
| **Write tests** | *"Write pytest tests for this function"* |
| **Suggest fixes** | *"How do I fix this ImportError?"* |
| **Understand projects** | *"What does this project do?"* — click 📁 first |
| **Hardware advice** | *"Can I run a 7B model on 8 GB?"* (it knows you can't) |

</div>

<br>

### What it can't do

<div align="center">

| ❌ Can't | Why |
|:---|:---|
| Browse the internet | Fully offline — that's the point |
| Run code for you | You press F5 |
| Edit files directly | Copy-paste from chat |
| See files you didn't share | Use 📎 for one file, 📁 for the project |
| Know the newest APIs | Training data has a cutoff |
| Replace Copilot / Cursor | It's 1.5B params. Use those tools for serious work |

</div>

<br>

### How to attach context

| Button | What it attaches | When to use |
|:---:|:---|:---|
| **📎** | Active file or selected text | *"Explain this"*, *"fix this function"* |
| **📁** | Whole project (tree + small files) | *"What does this do?"*, *"review the structure"* |

<br>

### The 8192-token reality

The model can only "see" about **2000 lines of code** at a time. For bigger projects, use 📎 on the specific file you need help with. You'll see `[chat] warning: project context is large` in the terminal when 📁 skips files.

---

<!-- ============================================================ -->
<!-- HARDWARE GUARDRAIL                                            -->
<!-- ============================================================ -->

## ⚠️ ML hardware guardrail

If your code uses **torch**, **tensorflow**, **transformers**, **.fit()**, or **nn.Module**, the IDE stops you before running it:

<div align="center">

<pre>
┌─────────────────────────────────────────────────────────────┐
│ ⚠  Hardware Guardrail                                       │
│                                                             │
│ Heavy ML/DL code detected.                                  │
│                                                             │
│ Detected: torch (PyTorch), nn.Module neural network         │
│                                                             │
│ Hardware profile:                                           │
│ • CPU: i5, 4 cores — training will saturate every core      │
│ • RAM: 8 GB — large models may swap or OOM                  │
│ • GPU: Intel UHD only — no CUDA                             │
│                                                             │
│ Suggestions: use CPU wheels, small batches, quantized       │
│ models, prefer inference over training.                     │
│                                                             │
│              [ Abort ]        [ Proceed Anyway ]            │
└─────────────────────────────────────────────────────────────┘
</pre>

</div>

**Why?** Because installing torch (2.5 GB) + trying to train a model on 8 GB RAM = wasted hours. This warning saves you from that.

**The IDE also auto-fixes torch installs:** if `requirements.txt` mentions torch, it writes a `pip.ini` that forces the **CPU-only wheel** (~200 MB) instead of the CUDA one (~2.5 GB). You never have to think about it.

---

<!-- ============================================================ -->
<!-- SHORTCUTS                                                     -->
<!-- ============================================================ -->

## ⌨️ Keyboard shortcuts

<div align="center">

| Shortcut | Action |
|:---|:---|
| <kbd>F5</kbd> | Run the active file |
| <kbd>Shift</kbd>+<kbd>F5</kbd> | Stop the running process |
| <kbd>Ctrl</kbd>+<kbd>S</kbd> | Save the active file |
| <kbd>F11</kbd> | Toggle fullscreen |
| <kbd>Ctrl</kbd>+<kbd>C</kbd> | Interrupt (in terminal) / Copy (with text selected) |
| <kbd>Enter</kbd> | Send chat message |

</div>

---

<!-- ============================================================ -->
<!-- WHAT IT CAN'T DO                                              -->
<!-- ============================================================ -->

## 🚫 What this IDE is NOT

Being honest so you don't waste time:

<div align="center">

| This is... | ...not this |
|:---|:---|
| A **bootstrap launcher** | A replacement for VS Code |
| A **first-file helper** | A full IDE with debugger, git, refactor |
| A **local AI assistant** | Copilot / Claude / Cursor |
| A **Python beginner tool** | An ML training framework |
| A **Windows app** | Cross-platform (Linux/Mac untested) |

</div>

<br>

### The editor is basic

- ✅ Line numbers, current-line highlight, tabs, save prompts
- ❌ No syntax highlighting
- ❌ No autocomplete
- ❌ No debugger
- ❌ No git integration

**That's why there's an "Open in VS Code" button.** The IDE gets you to "working project" — VS Code takes over from there.

---

<!-- ============================================================ -->
<!-- TROUBLESHOOTING                                               -->
<!-- ============================================================ -->

## 🔧 Troubleshooting

<div align="center">

| Problem | Fix |
|:---|:---|
| **"Python not found"** during build | Reinstall Python and tick **"Add Python to PATH"** |
| **Exe opens and closes instantly** | Check `dist\ai_ide\ai_ide_crash.log` for the error |
| **"Model not loaded"** in terminal | Check `dist\ai_ide\model\` contains the `.gguf` file |
| **"No system Python found"** | Add `C:\...\Python312\` to your PATH |
| **Windows Defender blocks the exe** | Add the `dist\` folder to Defender exclusions |
| **`ModuleNotFoundError: No module named 'flask'`** | Wait for `[pip] Dependencies installed.` before pressing F5 |
| **Ctrl+C does nothing** | Click into the black terminal panel first |
| **Chat says "model not loaded"** | Run `pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu` |
| **Django Run button does nothing** | Use VS Code's terminal: `.venv\Scripts\python.exe manage.py runserver` |

</div>

---

<!-- ============================================================ -->
<!-- REQUIREMENTS                                                  -->
<!-- ============================================================ -->

## 💻 System requirements

<div align="center">

| | Minimum | Recommended |
|:---|:---|:---|
| **OS** | Windows 10 | Windows 11 |
| **CPU** | 4 cores (i5 or better) | Any modern CPU |
| **RAM** | 8 GB | 16 GB |
| **Disk** | 3 GB free | 5 GB free |
| **Python** | 3.9+ | 3.11 or 3.12 |
| **GPU** | None (CPU-only) | None needed |

</div>

> 💡 **Built for the "aryan" workstation**: Intel Core i5, 4 cores, 8 GB RAM, integrated Intel UHD graphics, no CUDA GPU. If it runs here, it runs anywhere.

---

<!-- ============================================================ -->
<!-- FAQ                                                           -->
<!-- ============================================================ -->

## ❓ FAQ

<details>
<summary><b>Do I need to know Python to use this?</b></summary>

Nope. It's designed for people starting their first project. If you can double-click a `.exe`, you can use it.
</details>

<details>
<summary><b>Does the AI send my code anywhere?</b></summary>

No. Everything runs locally from a `.gguf` file on your disk. No internet, no API keys, no telemetry, no tracking. Disconnect your Wi-Fi and it still works.
</details>

<details>
<summary><b>Why is the model so big?</b></summary>

It's a quantized (compressed) version of Qwen2.5-Coder-1.5B. The full model is ~3 GB; the Q4_K_M version is ~1 GB with almost no quality loss. That's the smallest size that still gives useful code answers.
</details>

<details>
<summary><b>Can I use this on Mac or Linux?</b></summary>

The Python code should work but `build.bat` is Windows-only. You'd need to write a `build.sh` (mostly the same PyInstaller command). Untested.
</details>

<details>
<summary><b>How do I rebuild after changing ai_ide.py?</b></summary>

Double-click `build.bat` again. Takes ~2 minutes after the first build.
</details>

<details>
<summary><b>How do I uninstall?</b></summary>

Delete the folder. There's no registry entry, no system installation, no leftover files. It's fully portable.
</details>

<details>
<summary><b>Why Qwen2.5-Coder and not something else?</b></summary>

Qwen2.5-Coder-1.5B is the best small coding model that:
- Fits in 8 GB RAM
- Runs at usable speed on 4 CPU cores
- Has good Python knowledge
- Ships as GGUF (llama.cpp compatible)

Bigger models (7B+) would be too slow on this hardware.
</details>

<details>
<summary><b>Can I change the system prompt?</b></summary>

Yes — edit `SYSTEM_PROMPT` at the top of `ai_ide.py`, rebuild. The current prompt tells the AI it's on a CPU-only machine, which is why it never suggests CUDA code.
</details>

---

<!-- ============================================================ -->
<!-- CREDITS                                                       -->
<!-- ============================================================ -->

## 🙏 Credits

- **UI framework:** [PyQt6](https://pypi.org/project/PyQt6/)
- **AI model:** [Qwen2.5-Coder-1.5B-Instruct](https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct) by Alibaba
- **AI runtime:** [llama-cpp-python](https://github.com/abetlen/llama-cpp-python)
- **System monitor:** [psutil](https://github.com/giampaolo/psutil)
- **Packaging:** [PyInstaller](https://pyinstaller.org/)
- **Inspiration:** VS Code, Cursor, PyCharm's project wizards

---

<!-- ============================================================ -->
<!-- LICENSE                                                       -->
<!-- ============================================================ -->

## 📄 License

MIT — do whatever you want with it.

---

<div align="center">

### ⭐ If this saved you 10 minutes, star the repo

**Made with ⚡ and too much coffee**

<sub>Works offline · No cloud · No tracking · No API keys</sub>

</div>
