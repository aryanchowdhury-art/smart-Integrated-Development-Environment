#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ai_ide.py — Agentic Bootstrapper IDE for the "aryan" workstation.

Single-file PyQt6 application that:
  • loads model/qwen2.5-coder-1.5b-instruct-q4_k_m.gguf (n_ctx=8192) in a thread
  • monitors CPU / RAM / GPU vitals in real time (non-blocking HUD)
  • scaffolds new projects from 12 templates (general / web / data / ml / etc.)
  • lets you pick ANY location for the project, defaults to Desktop
  • auto-bootstraps .venv and auto-installs requirements.txt in the background
  • writes a CPU-torch pip.ini when a project asks for torch
  • guards against heavy ML/DL code on this CPU-only 8 GB machine
  • hands the workspace over to VS Code
  • local hardware-aware AI companion with 📎 file / 📁 project attach
  • responsive terminal with Ctrl+C interrupt and tree-kill stop button

Run:
    python ai_ide.py

Optional deps (app degrades gracefully without them):
    pip install PyQt6 psutil
    pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
"""

import html
import os
import re
import shutil
import subprocess
import sys
import traceback

from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal, QSize, QRect
from PyQt6.QtGui import (
    QFont,
    QFontMetricsF,
    QColor,
    QPainter,
    QTextFormat,
    QTextCursor,
    QAction,
    QKeySequence,
    QStandardItemModel,
    QStandardItem,
)
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QPlainTextEdit,
    QTextBrowser,
    QTextEdit,
    QLineEdit,
    QTabWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QFileDialog,
    QMessageBox,
    QDialog,
    QProgressBar,
    QSplitter,
    QFrame,
    QComboBox,
)

# ---------------------------------------------------------------------------
# Optional libraries
# ---------------------------------------------------------------------------
try:
    import psutil
except Exception:  # pragma: no cover
    psutil = None


# ---------------------------------------------------------------------------
# Theme — VS Code dark
# ---------------------------------------------------------------------------
BG = "#1e1e1e"
SIDEBAR = "#252526"
BORDER = "#333333"
ACCENT = "#0e639c"
TEXT = "#d4d4d4"
MUTED = "#9d9d9d"
ERROR = "#f48771"

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_FILENAME = "qwen2.5-coder-1.5b-instruct-q4_k_m.gguf"

SKIP_DIRS = {
    ".venv", "venv", "__pycache__", ".git", "node_modules",
    ".idea", ".vscode", ".mypy_cache", ".pytest_cache", ".next",
    ".tox", ".eggs", "build", "dist", "*.egg-info",
}

SYSTEM_PROMPT = (
    'You are the built-in AI companion of the "Agentic Bootstrapper IDE". '
    'You run locally inside the IDE on a machine named "aryan". '
    'Hardware profile of aryan: Intel Core i5, 4 CPU cores, 8 GB RAM, '
    'integrated Intel UHD graphics, NO CUDA GPU. '
    'Rules: always give CPU-friendly, memory-light advice; prefer small batch sizes, '
    'quantized models, and inference over training; avoid recommending GPU/CUDA-only code; '
    'keep answers short, practical, and ready to paste into the editor. '
    'If the user asks for something that will not fit the hardware, explain the limit '
    'and offer a lighter alternative.'
)

ML_PATTERNS = [
    (r"\btorch\b", "torch (PyTorch)"),
    (r"\btensorflow\b", "tensorflow"),
    (r"\btransformers\b", "HuggingFace transformers"),
    (r"\bfit\s*\(", ".fit(...) training call"),
    (r"\bnn\.Module\b", "nn.Module neural network"),
]

TEXT_EXTS = {
    ".py", ".txt", ".md", ".json", ".toml", ".cfg", ".ini",
    ".yaml", ".yml", ".html", ".css", ".js", ".sql",
    ".sh", ".bat", ".ps1", ".env", ".gitignore",
}


# ---------------------------------------------------------------------------
# Project templates
# ---------------------------------------------------------------------------
# ── General ─────────────────────────────────────────────────────────────
PY_SCRIPT_MAIN = '''"""Simple Python script — press F5 in the IDE to run."""
from datetime import datetime


def main():
    print("Hello from Python!")
    print(f"Run at: {datetime.now().isoformat(timespec='seconds')}")


if __name__ == "__main__":
    main()
'''

CLI_TOOL_PY = '''"""Command-line tool using argparse."""
import argparse
import sys


def build_parser():
    parser = argparse.ArgumentParser(
        description="A simple CLI tool.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("name", nargs="?", default="world", help="who to greet")
    parser.add_argument("-c", "--count", type=int, default=1, help="how many times")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    for _ in range(args.count):
        print(f"Hello, {args.name}!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''


# ── Web ─────────────────────────────────────────────────────────────────
FLASK_APP_PY = '''from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

notes = [{"id": 1, "title": "Welcome", "body": "Edit app.py to make this yours."}]

@app.route("/")
def home():
    return render_template("index.html", notes=notes)

@app.route("/api/notes", methods=["GET"])
def list_notes():
    return jsonify(notes)

@app.route("/api/notes", methods=["POST"])
def add_note():
    data = request.get_json(force=True, silent=True) or {}
    title = (data.get("title") or "").strip()
    body = (data.get("body") or "").strip()
    if not title:
        return jsonify({"error": "title required"}), 400
    note = {"id": len(notes) + 1, "title": title, "body": body}
    notes.append(note)
    return jsonify(note), 201

@app.route("/health")
def health():
    return jsonify({"status": "ok", "notes": len(notes)})

if __name__ == "__main__":
    # debug=False keeps a single process so the IDE can stop it cleanly.
    app.run(host="127.0.0.1", port=5000, debug=False)
'''

FLASK_REQUIREMENTS = "flask>=3.0\n"

FLASK_INDEX_HTML = '''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Flask App</title>
  <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
  <h1>📝 Notes</h1>
  <ul>
    {% for note in notes %}
      <li><strong>{{ note.title }}</strong> — {{ note.body }}</li>
    {% endfor %}
  </ul>
  <p>Try: <a href="/health">/health</a> · <a href="/api/notes">/api/notes</a></p>
</body>
</html>
'''

FLASK_STYLE_CSS = '''body {
  background: #1e1e1e;
  color: #d4d4d4;
  font-family: Consolas, monospace;
  max-width: 640px;
  margin: 40px auto;
}
a { color: #0e639c; }
'''

FASTAPI_MAIN = '''"""FastAPI starter with a small in-memory store."""
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="FastAPI Test")


class Item(BaseModel):
    name: str
    price: float


items: list[Item] = []


@app.get("/")
def root():
    return {"status": "ok", "items": len(items)}


@app.get("/items")
def list_items():
    return items


@app.post("/items")
def add_item(item: Item):
    items.append(item)
    return {"added": item, "total": len(items)}


if __name__ == "__main__":
    import uvicorn
    # reload=False keeps a single process so the IDE can stop it cleanly.
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
'''

FASTAPI_REQUIREMENTS = "fastapi>=0.110\nuvicorn[standard]>=0.27\npydantic>=2.0\n"

DJANGO_MANAGE_PY = '''#!/usr/bin/env python
"""Django's command-line utility."""
import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Run 'Install Reqs' in the IDE first."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
'''

DJANGO_SETTINGS = '''"""Minimal Django settings for a starter project."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "django-insecure-change-me-in-production"
DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "home",
]

MIDDLEWARE = [
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "mysite.urls"

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": []},
}]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

STATIC_URL = "static/"
USE_TZ = True
'''

DJANGO_URLS = '''from django.urls import path
from home import views

urlpatterns = [
    path("", views.home, name="home"),
]
'''

DJANGO_HOME_VIEWS = '''from django.http import JsonResponse


def home(request):
    return JsonResponse({"status": "ok", "message": "Django is running"})
'''

DJANGO_README = '''# Django Starter

> **Run this project** with the IDE's **Open in VS Code** button (or any
> terminal) and:
>
> ```powershell
> .venv\\Scripts\\python.exe manage.py runserver
> ```
>
> Then open <http://127.0.0.1:8000/>.
>
> The IDE's ▶ Run Script button won't work directly — Django needs the
> `runserver` argument. Run it from VS Code's terminal or the standalone
> terminal instead.

A minimal Django project with one JSON endpoint. Add apps with:

```powershell
.venv\\Scripts\\python.exe manage.py startapp myapp
```
'''

DJANGO_REQUIREMENTS = "django>=5.0\n"


# ── Data & ML ───────────────────────────────────────────────────────────
DATA_SCIENCE_MAIN = '''"""Data analysis starter — pandas + numpy on CPU."""
import numpy as np
import pandas as pd


def make_data(n=100, seed=0):
    rng = np.random.default_rng(seed)
    return pd.DataFrame({
        "x": np.arange(n),
        "y": np.arange(n) * 2 + rng.standard_normal(n),
        "group": rng.choice(["A", "B", "C"], size=n),
    })


def summarize(df):
    print(f"Shape: {df.shape}")
    print("\\nHead:")
    print(df.head())
    print("\\nDescribe:")
    print(df.describe())
    print("\\nGroup means:")
    print(df.groupby("group")[["x", "y"]].mean())


if __name__ == "__main__":
    data = make_data()
    summarize(data)
    print("\\nTip: this machine has 8 GB RAM — keep DataFrames small (< 1 GB).")
'''

DATA_SCIENCE_REQUIREMENTS = "pandas>=2.0\nnumpy>=1.26\nmatplotlib>=3.8\n"

ML_MAIN_PY = '''"""Light ML starter tuned for the aryan machine (i5, 8GB, no CUDA).

Prefer sklearn / numpy workflows. Reach for torch only after checking
RAM headroom in the IDE HUD — and keep batch sizes small.
"""
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression


def demo():
    rng = np.random.default_rng(0)
    data = pd.DataFrame({
        "x": np.arange(50),
        "y": np.arange(50) * 2 + rng.standard_normal(50),
    })
    model = LinearRegression().fit(data[["x"]], data["y"])
    print("Slope:", round(float(model.coef_[0]), 4))
    print("Intercept:", round(float(model.intercept_), 4))
    print()
    print("Reminder: this machine has 8 GB RAM and no CUDA GPU.")
    print("Prefer sklearn for tabular work; small quantized models for LLM inference.")


if __name__ == "__main__":
    demo()
'''

ML_REQUIREMENTS = "numpy>=1.26\npandas>=2.0\nscikit-learn>=1.4\n"

ML_GUARDRAIL_DEMO = '''"""Guardrail demo — Run this file to see the hardware warning.

It contains heavy ML keywords on purpose. Nothing here executes unless you
choose "Proceed Anyway" AND have torch installed (you likely won't).
"""
import torch
import torch.nn as nn


class TinyNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc = nn.Linear(10, 1)

    def forward(self, x):
        return self.fc(x)


if __name__ == "__main__":
    net = TinyNet()
    net(torch.randn(1, 10))
    print("guardrail test — this should be blocked by the IDE first")
'''


# ── Automation ──────────────────────────────────────────────────────────
SCRAPER_MAIN = '''"""Minimal web scraper — requests + BeautifulSoup."""
import requests
from bs4 import BeautifulSoup


def scrape(url, selector):
    resp = requests.get(
        url, timeout=15, headers={"User-Agent": "aryan-bootstrapper/1.0"}
    )
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    return [el.get_text(strip=True) for el in soup.select(selector)]


if __name__ == "__main__":
    url = "https://example.com"
    items = scrape(url, "h1")
    print(f"Scraped from {url}:")
    for item in items:
        print(f"  - {item}")
    print("\\nTip: be polite — add delays between requests on real sites.")
'''

SCRAPER_REQUIREMENTS = "requests>=2.31\nbeautifulsoup4>=4.12\n"


# ── Desktop ─────────────────────────────────────────────────────────────
TKINTER_APP = '''"""A tiny Tkinter GUI — runs on the built-in Python, no installs needed."""
import tkinter as tk
from tkinter import ttk


def main():
    root = tk.Tk()
    root.title("Tkinter Starter")
    root.geometry("420x220")

    ttk.Label(root, text="Enter your name:").pack(pady=(20, 6))
    name_var = tk.StringVar(value="world")
    entry = ttk.Entry(root, textvariable=name_var, width=28)
    entry.pack()

    greeting = ttk.Label(root, text="", font=("Segoe UI", 12))
    greeting.pack(pady=14)

    def on_greet():
        greeting.config(text=f"Hello, {name_var.get() or 'world'}!")

    ttk.Button(root, text="Greet", command=on_greet).pack()
    entry.focus_set()
    entry.bind("<Return>", lambda _e: on_greet())

    root.mainloop()


if __name__ == "__main__":
    main()
'''


# ── Library ─────────────────────────────────────────────────────────────
PKG_PYPROJECT = '''[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "mypkg"
version = "0.1.0"
description = "A small installable Python package."
readme = "README.md"
requires-python = ">=3.9"
authors = [{ name = "Your Name", email = "you@example.com" }]
dependencies = []

[tool.setuptools.packages.find]
where = ["."]
include = ["mypkg*"]
'''

PKG_INIT = '''"""My package."""
from .core import greet

__all__ = ["greet"]
__version__ = "0.1.0"
'''

PKG_CORE = '''"""Core functionality."""


def greet(name: str = "world") -> str:
    """Return a greeting string."""
    return f"Hello, {name}!"


if __name__ == "__main__":
    print(greet())
'''

PKG_README = '''# mypkg

A small installable Python package.

## Install (editable)

```powershell
.venv\\Scripts\\python.exe -m pip install -e .
```

## Use

```python
from mypkg import greet
print(greet("aryan"))
```
'''


# ── Testing ─────────────────────────────────────────────────────────────
PYTEST_TESTS = '''"""Sample pytest tests. Press F5 in the IDE to run them."""
import pytest


def add(a, b):
    return a + b


def test_add_positive():
    assert add(2, 3) == 5


def test_add_negative():
    assert add(-1, -1) == -2


def test_add_zero():
    assert add(0, 0) == 0


@pytest.mark.parametrize("a,b,expected", [(1, 1, 2), (2, 2, 4), (10, -5, 5)])
def test_add_parametrized(a, b, expected):
    assert add(a, b) == expected


if __name__ == "__main__":
    # Lets `python test_sample.py` also work as a quick self-check.
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
'''

PYTEST_REQUIREMENTS = "pytest>=8.0\n"


# ── Template registry ──────────────────────────────────────────────────
TEMPLATES = {
    "Empty Project": {},
    "Python Script": {
        "main.py": PY_SCRIPT_MAIN,
    },
    "CLI Tool (argparse)": {
        "cli.py": CLI_TOOL_PY,
    },
    "Flask Web App": {
        "app.py": FLASK_APP_PY,
        "requirements.txt": FLASK_REQUIREMENTS,
        os.path.join("templates", "index.html"): FLASK_INDEX_HTML,
        os.path.join("static", "style.css"): FLASK_STYLE_CSS,
    },
    "FastAPI Web API": {
        "main.py": FASTAPI_MAIN,
        "requirements.txt": FASTAPI_REQUIREMENTS,
    },
    "Django Web App": {
        "manage.py": DJANGO_MANAGE_PY,
        os.path.join("mysite", "__init__.py"): "",
        os.path.join("mysite", "settings.py"): DJANGO_SETTINGS,
        os.path.join("mysite", "urls.py"): DJANGO_URLS,
        os.path.join("home", "__init__.py"): "",
        os.path.join("home", "views.py"): DJANGO_HOME_VIEWS,
        "requirements.txt": DJANGO_REQUIREMENTS,
        "README.md": DJANGO_README,
    },
    "Data Science (pandas)": {
        "analysis.py": DATA_SCIENCE_MAIN,
        "requirements.txt": DATA_SCIENCE_REQUIREMENTS,
    },
    "ML Starter (sklearn CPU)": {
        "main.py": ML_MAIN_PY,
        "guardrail_demo.py": ML_GUARDRAIL_DEMO,
        "requirements.txt": ML_REQUIREMENTS,
    },
    "Web Scraper": {
        "scraper.py": SCRAPER_MAIN,
        "requirements.txt": SCRAPER_REQUIREMENTS,
    },
    "Tkinter GUI": {
        "app.py": TKINTER_APP,
    },
    "Package (setuptools)": {
        "pyproject.toml": PKG_PYPROJECT,
        os.path.join("mypkg", "__init__.py"): PKG_INIT,
        os.path.join("mypkg", "core.py"): PKG_CORE,
        "README.md": PKG_README,
    },
    "Pytest Test Suite": {
        "test_sample.py": PYTEST_TESTS,
        "requirements.txt": PYTEST_REQUIREMENTS,
    },
}

TEMPLATE_CATALOG = [
    ("── General ──", None),
    ("Empty Project", "Empty Project"),
    ("Python Script", "Python Script"),
    ("CLI Tool (argparse)", "CLI Tool (argparse)"),
    ("── Web ──", None),
    ("Flask Web App", "Flask Web App"),
    ("FastAPI Web API", "FastAPI Web API"),
    ("Django Web App", "Django Web App"),
    ("── Data & ML ──", None),
    ("Data Science (pandas)", "Data Science (pandas)"),
    ("ML Starter (sklearn CPU)", "ML Starter (sklearn CPU)"),
    ("── Automation ──", None),
    ("Web Scraper", "Web Scraper"),
    ("── Desktop ──", None),
    ("Tkinter GUI", "Tkinter GUI"),
    ("── Library ──", None),
    ("Package (setuptools)", "Package (setuptools)"),
    ("── Testing ──", None),
    ("Pytest Test Suite", "Pytest Test Suite"),
]


# ---------------------------------------------------------------------------
# Stylesheet
# ---------------------------------------------------------------------------
STYLESHEET = """
QMainWindow, QDialog { background-color: #1e1e1e; }
QWidget { color: #d4d4d4; }
QFrame#hud { background-color: #252526; border: none; border-bottom: 1px solid #333333; }
QFrame#panel { background-color: #252526; border: none; }
QPushButton {
    background-color: #0e639c; color: #ffffff; border: none;
    border-radius: 3px; padding: 6px 12px;
}
QPushButton:hover { background-color: #1177bb; }
QPushButton:pressed { background-color: #0d5a8c; }
QPushButton:disabled { background-color: #3c3c3c; color: #7a7a7a; }
QPushButton#secondary { background-color: #3c3c3c; color: #d4d4d4; }
QPushButton#secondary:hover { background-color: #4a4a4a; }
QPushButton#secondary:checked { background-color: #0e639c; color: #ffffff; }
QPushButton#run { background-color: #16825d; }
QPushButton#run:hover { background-color: #1a9c6f; }
QPushButton#run:disabled { background-color: #2e5c48; color: #7a9d8f; }
QPushButton#stop { background-color: #a1260d; }
QPushButton#stop:hover { background-color: #c42b1c; }
QPushButton#stop:pressed { background-color: #8a1f0a; }
QPushButton#stop:disabled { background-color: #3c3c3c; color: #7a7a7a; }
QLineEdit {
    background-color: #3c3c3c; border: 1px solid #3c3c3c;
    padding: 5px; border-radius: 2px; color: #d4d4d4;
    selection-background-color: #094771;
}
QLineEdit:focus { border: 1px solid #0e639c; }
QComboBox {
    background-color: #3c3c3c; color: #d4d4d4;
    border: 1px solid #3c3c3c; padding: 5px 10px; border-radius: 2px;
}
QComboBox::drop-down { border: none; width: 20px; }
QComboBox QAbstractItemView {
    background-color: #2d2d2d; color: #d4d4d4;
    selection-background-color: #094771; border: 1px solid #333333;
}
QPlainTextEdit, QTextBrowser {
    background-color: #1e1e1e; border: none; color: #d4d4d4;
    selection-background-color: #094771;
}
QTreeWidget { background-color: #252526; border: none; outline: none; }
QTreeWidget::item { padding: 4px; }
QTreeWidget::item:hover { background-color: #2a2d2e; }
QTreeWidget::item:selected { background-color: #094771; }
QTabWidget::pane { border: 1px solid #333333; background: #1e1e1e; }
QTabBar::tab { background: #2d2d2d; color: #9d9d9d; padding: 6px 14px; border: none; }
QTabBar::tab:selected { background: #1e1e1e; color: #ffffff; border-top: 1px solid #0e639c; }
QTabBar::tab:hover { color: #ffffff; }
QSplitter::handle { background-color: #333333; }
QSplitter::handle:horizontal { width: 1px; }
QSplitter::handle:vertical { height: 1px; }
QScrollBar:vertical { background: #1e1e1e; width: 12px; }
QScrollBar::handle:vertical { background: #424242; min-height: 20px; border-radius: 6px; }
QScrollBar::handle:vertical:hover { background: #4f4f4f; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
QScrollBar:horizontal { background: #1e1e1e; height: 12px; }
QScrollBar::handle:horizontal { background: #424242; min-width: 20px; border-radius: 6px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }
QProgressBar { border: 1px solid #333333; background: #1e1e1e; border-radius: 2px; }
QProgressBar::chunk { background-color: #0e639c; }
QDialog#splash { background-color: #252526; border: 1px solid #0e639c; }
QDialog#selector { background-color: #252526; border: 1px solid #333333; }
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def resolve_model_path():
    candidates = [
        os.path.join(BASE_DIR, "model", MODEL_FILENAME),
        os.path.join(os.getcwd(), "model", MODEL_FILENAME),
        os.path.join(BASE_DIR, MODEL_FILENAME),
    ]
    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate
    return candidates[0]


def detect_gpu():
    try:
        import GPUtil  # noqa: F401
        gpus = GPUtil.getGPUs()
        if gpus:
            return gpus[0].name
    except Exception:
        pass
    return "Integrated UHD (No CUDA)"


def sanitize_folder_name(name):
    return re.sub(r'[<>:"/\\|?*]', "", name).strip()


def find_venv_python(project_dir):
    if os.name == "nt":
        candidate = os.path.join(project_dir, ".venv", "Scripts", "python.exe")
    else:
        candidate = os.path.join(project_dir, ".venv", "bin", "python")
    return candidate if os.path.isfile(candidate) else None


def find_system_python():
    if not getattr(sys, "frozen", False):
        return sys.executable
    for name in ("python", "python3"):
        found = shutil.which(name)
        if found:
            return found
    if os.name == "nt":
        for ver in ("313", "312", "311", "310", "39"):
            path = os.path.expandvars(
                r"%LOCALAPPDATA%\Programs\Python\Python" + ver + r"\python.exe"
            )
            if os.path.isfile(path):
                return path
    return None


def subprocess_kwargs():
    kwargs = dict(
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        encoding="utf-8",
        errors="replace",
    )
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
    return kwargs


def scaffold_project(path, template):
    """Create starter files inside `path` based on template name. Never overwrites."""
    files = TEMPLATES.get(template, {})
    for rel, content in files.items():
        full = os.path.join(path, rel)
        parent = os.path.dirname(full)
        if parent:
            os.makedirs(parent, exist_ok=True)
        if not os.path.exists(full):
            with open(full, "w", encoding="utf-8") as handle:
                handle.write(content)


def build_editor_context(editor, max_chars=6000):
    """Return a chat-friendly snippet of the active editor buffer, or None."""
    if editor is None:
        return None
    cursor = editor.textCursor()
    if cursor.hasSelection():
        code = cursor.selectedText()
    else:
        code = editor.toPlainText().strip()
    if not code:
        return None
    path = getattr(editor, "file_path", None)
    name = os.path.basename(path) if path else "untitled"
    lang = "python" if name.endswith(".py") else ""
    if len(code) > max_chars:
        head = code[: max_chars // 2]
        tail = code[-max_chars // 2:]
        code = f"{head}\n\n# ... [{len(code) - max_chars} chars elided] ...\n\n{tail}"
    return f"[Active file: {name}]\n```{lang}\n{code}\n```"


def build_project_context(project_dir, budget_chars=18000, max_file_chars=4000):
    """Build a compact snapshot: tree + contents of small text files.
    Returns (bundle_string, stats_dict)."""
    header = [
        f"[Project: {os.path.basename(project_dir)}]",
        f"[Root: {project_dir}]",
        "",
        "=== TREE ===",
    ]
    tree_lines = []
    file_paths = []

    def walk(path, depth=0):
        if depth > 4:
            return
        try:
            entries = sorted(os.listdir(path))
        except Exception:
            return
        dirs = [
            e for e in entries
            if os.path.isdir(os.path.join(path, e)) and e not in SKIP_DIRS
        ]
        files = [e for e in entries if os.path.isfile(os.path.join(path, e))]
        indent = "  " * depth
        for d in dirs:
            tree_lines.append(f"{indent}{d}/")
            walk(os.path.join(path, d), depth + 1)
        for f in files:
            full = os.path.join(path, f)
            try:
                size = os.path.getsize(full)
            except Exception:
                size = 0
            tree_lines.append(f"{indent}{f}  ({size} bytes)")
            file_paths.append(full)

    walk(project_dir)

    used = sum(len(line) + 1 for line in header)
    used += sum(len(line) + 1 for line in tree_lines)
    body = ["", "=== FILES ==="]
    used += 16

    files_included = 0
    files_skipped = 0

    for path in file_paths:
        ext = os.path.splitext(path)[1].lower()
        if ext not in TEXT_EXTS:
            files_skipped += 1
            continue
        rel = os.path.relpath(path, project_dir)
        try:
            if os.path.getsize(path) > max_file_chars * 4:
                files_skipped += 1
                continue
            with open(path, "r", encoding="utf-8", errors="replace") as handle:
                content = handle.read()
        except Exception:
            files_skipped += 1
            continue

        if len(content) > max_file_chars:
            content = (
                content[:max_file_chars]
                + f"\n... [{len(content) - max_file_chars} chars elided] ..."
            )

        chunk = f"\n--- {rel} ---\n```\n{content}\n```\n"
        if used + len(chunk) > budget_chars:
            files_skipped += 1
            continue
        body.append(chunk)
        used += len(chunk)
        files_included += 1

    if files_skipped:
        body.append(f"\n[+ {files_skipped} file(s) skipped to fit the context budget]")

    bundle = "\n".join(header + tree_lines + body)
    stats = {
        "files_included": files_included,
        "files_skipped": files_skipped,
        "chars_used": used,
        "tree_lines": len(tree_lines),
        "est_tokens": used // 3,
    }
    return bundle, stats


# ---------------------------------------------------------------------------
# Background threads
# ---------------------------------------------------------------------------
class ModelLoaderThread(QThread):
    progress = pyqtSignal(str)
    loaded = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, model_path, parent=None):
        super().__init__(parent)
        self.model_path = model_path

    def run(self):
        self.progress.emit("Verifying workspace environment...")
        self.msleep(200)
        self.progress.emit("Checking Python packages (llama-cpp-python)...")
        try:
            from llama_cpp import Llama
        except Exception as exc:
            self.failed.emit(
                "llama-cpp-python is not installed.\n"
                "Install a CPU wheel with:\n"
                "  pip install llama-cpp-python --extra-index-url "
                "https://abetlen.github.io/llama-cpp-python/whl/cpu\n\n"
                f"Details: {exc!r}"
            )
            return

        if not os.path.isfile(self.model_path):
            self.failed.emit(f"Model file not found:\n{self.model_path}")
            return

        self.progress.emit("Loading model into memory (n_ctx=8192, n_threads=4)...")
        try:
            model = Llama(
                model_path=self.model_path,
                n_ctx=8192,
                n_threads=4,
                n_batch=256,
                verbose=False,
            )
        except Exception as exc:
            self.failed.emit(f"Failed to load model:\n{exc!r}")
            return

        self.progress.emit("Model ready.")
        self.loaded.emit(model)


class HardwareMonitorThread(QThread):
    vitals = pyqtSignal(float, float, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = True

    def run(self):
        gpu = detect_gpu()
        if psutil is None:
            while self._running:
                self.vitals.emit(-1.0, -1.0, gpu)
                self.msleep(1000)
            return
        try:
            psutil.cpu_percent(interval=None)
        except Exception:
            pass
        while self._running:
            try:
                cpu = float(psutil.cpu_percent(interval=None))
                ram = float(psutil.virtual_memory().percent)
            except Exception:
                cpu, ram = -1.0, -1.0
            self.vitals.emit(cpu, ram, gpu)
            for _ in range(15):
                if not self._running:
                    break
                self.msleep(100)

    def stop(self):
        self._running = False


class ScriptRunnerThread(QThread):
    output = pyqtSignal(str)
    run_finished = pyqtSignal(int)

    def __init__(self, python_exe, script_path, cwd, parent=None):
        super().__init__(parent)
        self.python_exe = python_exe
        self.script_path = script_path
        self.cwd = cwd
        self.proc = None
        self._stop = False

    def run(self):
        try:
            kwargs = subprocess_kwargs()
            kwargs["cwd"] = self.cwd
            self.proc = subprocess.Popen([self.python_exe, self.script_path], **kwargs)
            assert self.proc.stdout is not None
            for line in self.proc.stdout:
                self.output.emit(line.rstrip("\n"))
                if self._stop:
                    break
            self.proc.wait()
            code = self.proc.returncode if self.proc.returncode is not None else -1
            self.run_finished.emit(code)
        except Exception as exc:
            self.output.emit(f"[run] error: {exc!r}")
            self.run_finished.emit(-1)

    def stop(self):
        self._stop = True
        if self.proc is None or self.proc.poll() is not None:
            return
        try:
            if os.name == "nt":
                # /T kills the entire process tree (parent + any children),
                # /F forces it. Handles Flask reloader children if debug=True.
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(self.proc.pid)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
            else:
                self.proc.terminate()
        except Exception:
            try:
                self.proc.terminate()
            except Exception:
                pass


class VenvSetupThread(QThread):
    output = pyqtSignal(str)
    setup_finished = pyqtSignal(bool, str)

    def __init__(self, base_python, project_dir, parent=None):
        super().__init__(parent)
        self.base_python = base_python
        self.project_dir = project_dir

    def _venv_python(self):
        return find_venv_python(self.project_dir) or (
            os.path.join(self.project_dir, ".venv", "Scripts", "python.exe")
            if os.name == "nt"
            else os.path.join(self.project_dir, ".venv", "bin", "python")
        )

    def _run(self, cmd):
        kwargs = subprocess_kwargs()
        kwargs["cwd"] = self.project_dir
        try:
            proc = subprocess.Popen(cmd, **kwargs)
            assert proc.stdout is not None
            for line in proc.stdout:
                self.output.emit(line.rstrip("\n"))
            proc.wait()
            return proc.returncode
        except Exception as exc:
            self.output.emit(f"[venv] command failed: {exc!r}")
            return -1

    def _maybe_write_cpu_pip_ini(self):
        """Write a per-venv pip config for torch projects to force CPU wheels."""
        req = os.path.join(self.project_dir, "requirements.txt")
        if not os.path.isfile(req):
            return
        try:
            with open(req, "r", encoding="utf-8") as handle:
                content = handle.read().lower()
        except Exception:
            return
        if "torch" not in content:
            return
        ini_name = "pip.ini" if os.name == "nt" else "pip.conf"
        ini_path = os.path.join(self.project_dir, ".venv", ini_name)
        try:
            os.makedirs(os.path.dirname(ini_path), exist_ok=True)
            with open(ini_path, "w", encoding="utf-8") as handle:
                handle.write(
                    "[global]\n"
                    "extra-index-url = https://download.pytorch.org/whl/cpu\n"
                )
            self.output.emit(f"[venv] wrote CPU-torch index to {ini_path}")
        except Exception as exc:
            self.output.emit(f"[venv] could not write pip config: {exc!r}")

    def run(self):
        try:
            venv_dir = os.path.join(self.project_dir, ".venv")
            vpy = self._venv_python()

            if not os.path.isfile(vpy):
                self.output.emit(f"[venv] creating virtual environment at {venv_dir}")
                rc = self._run([self.base_python, "-m", "venv", venv_dir])
                if rc != 0:
                    self.setup_finished.emit(
                        False, "Failed to create virtual environment."
                    )
                    return
            else:
                self.output.emit("[venv] virtual environment already exists, reusing it.")

            # Self-heal: make sure pip is actually present before upgrading it.
            try:
                check = subprocess.run(
                    [vpy, "-m", "pip", "--version"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                pip_ok = check.returncode == 0
            except Exception:
                pip_ok = False

            if not pip_ok:
                self.output.emit("[venv] pip missing — running ensurepip")
                rc = self._run([vpy, "-m", "ensurepip", "--upgrade"])
                if rc != 0:
                    self.output.emit("[venv] ensurepip failed — fetching get-pip.py")
                    rc = self._run([vpy, "https://bootstrap.pypa.io/get-pip.py"])
                    if rc != 0:
                        self.setup_finished.emit(
                            False,
                            "pip bootstrap failed. Install python3-venv or "
                            "reinstall Python with ensurepip available.",
                        )
                        return

            self._maybe_write_cpu_pip_ini()

            self.output.emit("[venv] upgrading pip / setuptools / wheel ...")
            rc = self._run(
                [vpy, "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"]
            )
            if rc != 0:
                self.setup_finished.emit(False, "pip upgrade failed.")
                return

            self.setup_finished.emit(True, vpy)
        except Exception as exc:
            self.output.emit(f"[venv] error: {exc!r}")
            self.setup_finished.emit(False, repr(exc))


class PipInstallThread(QThread):
    output = pyqtSignal(str)
    install_finished = pyqtSignal(bool, str)

    def __init__(self, venv_python, project_dir, parent=None):
        super().__init__(parent)
        self.venv_python = venv_python
        self.project_dir = project_dir

    def run(self):
        req = os.path.join(self.project_dir, "requirements.txt")
        if not os.path.isfile(req):
            self.install_finished.emit(False, "No requirements.txt in this project.")
            return
        try:
            kwargs = subprocess_kwargs()
            kwargs["cwd"] = self.project_dir
            proc = subprocess.Popen(
                [self.venv_python, "-m", "pip", "install", "-r", req],
                **kwargs,
            )
            assert proc.stdout is not None
            for line in proc.stdout:
                self.output.emit(line.rstrip("\n"))
            proc.wait()
            ok = proc.returncode == 0
            self.install_finished.emit(
                ok,
                "Dependencies installed." if ok
                else f"pip exited with code {proc.returncode}.",
            )
        except Exception as exc:
            self.output.emit(f"[pip] error: {exc!r}")
            self.install_finished.emit(False, repr(exc))


class ChatThread(QThread):
    token = pyqtSignal(str)
    error = pyqtSignal(str)
    chat_done = pyqtSignal()

    def __init__(self, model, system_prompt, history, parent=None):
        super().__init__(parent)
        self.model = model
        self.system_prompt = system_prompt
        self.history = history

    def run(self):
        try:
            messages = [{"role": "system", "content": self.system_prompt}] + self.history
            stream = self.model.create_chat_completion(
                messages=messages,
                max_tokens=512,
                temperature=0.4,
                top_p=0.9,
                stream=True,
            )
            for chunk in stream:
                try:
                    delta = chunk["choices"][0].get("delta", {})
                except Exception:
                    continue
                piece = delta.get("content")
                if piece:
                    self.token.emit(piece)
        except Exception as exc:
            self.error.emit(repr(exc))
        finally:
            self.chat_done.emit()


# ---------------------------------------------------------------------------
# Terminal widget with Ctrl+C interrupt
# ---------------------------------------------------------------------------
class TerminalView(QPlainTextEdit):
    """Read-only terminal that forwards Ctrl+C as an interrupt signal."""

    interrupt_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setFont(QFont("Consolas", 10))
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def keyPressEvent(self, event):
        if (
            event.key() == Qt.Key.Key_C
            and event.modifiers() == Qt.KeyboardModifier.ControlModifier
            and not self.textCursor().hasSelection()
        ):
            self.interrupt_requested.emit()
            return
        super().keyPressEvent(event)


# ---------------------------------------------------------------------------
# Editor widget with line-number gutter
# ---------------------------------------------------------------------------
class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.editor.line_number_area_paint_event(event)


class CodeEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.file_path = None
        self.line_number_area = LineNumberArea(self)

        font = QFont("Consolas")
        font.setStyleHint(QFont.StyleHint.Monospace)
        font.setPointSize(11)
        self.setFont(font)
        self.setTabStopDistance(QFontMetricsF(self.font()).horizontalAdvance(" ") * 4)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)

        self.update_line_number_area_width(0)
        self.highlight_current_line()

    def line_number_area_width(self):
        digits = len(str(max(1, self.blockCount())))
        return 12 + self.fontMetrics().horizontalAdvance("9") * digits

    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(
                0, rect.y(), self.line_number_area.width(), rect.height()
            )
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height())
        )

    def line_number_area_paint_event(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor(SIDEBAR))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        painter.setPen(QColor("#858585"))
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.drawText(
                    0,
                    int(top),
                    self.line_number_area.width() - 6,
                    self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight,
                    number,
                )
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1

    def highlight_current_line(self):
        extra = QTextEdit.ExtraSelection()
        extra.format.setBackground(QColor("#282828"))
        extra.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
        extra.cursor = self.textCursor()
        extra.cursor.clearSelection()
        self.setExtraSelections([extra])


# ---------------------------------------------------------------------------
# Splash screen
# ---------------------------------------------------------------------------
class SplashScreen(QDialog):
    def __init__(self):
        super().__init__(None)
        self.setObjectName("splash")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setFixedSize(560, 300)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(10)

        title = QLabel("AGENTIC BOOTSTRAPPER IDE")
        title.setStyleSheet(
            "color:#ffffff; font-size:20px; font-weight:bold; letter-spacing:2px;"
        )
        subtitle = QLabel("Initializing AI Workspace for machine 'aryan'")
        subtitle.setStyleSheet("color:#9d9d9d; font-size:12px;")

        self.status = QLabel("Starting...")
        self.status.setStyleSheet("color:#0e639c; font-size:12px; padding-top:10px;")
        self.status.setWordWrap(True)

        bar = QProgressBar()
        bar.setRange(0, 0)
        bar.setTextVisible(False)
        bar.setFixedHeight(6)

        spec = QLabel(
            "Target hardware:  Intel Core i5 (4 cores)  ·  8 GB RAM  ·  "
            "Intel UHD graphics (no CUDA)"
        )
        spec.setStyleSheet("color:#6f6f6f; font-size:11px; padding-top:8px;")
        spec.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addStretch(1)
        layout.addWidget(self.status)
        layout.addWidget(bar)
        layout.addStretch(1)
        layout.addWidget(spec)

        screen = QApplication.primaryScreen()
        if screen is not None:
            geo = screen.availableGeometry()
            self.move(
                geo.x() + (geo.width() - self.width()) // 2,
                geo.y() + (geo.height() - self.height()) // 2,
            )

    def set_message(self, text):
        self.status.setText(text)


# ---------------------------------------------------------------------------
# Project selector (with location picker + grouped templates)
# ---------------------------------------------------------------------------
class ProjectSelector(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("selector")
        self.setWindowTitle("Select Project")
        self.setModal(True)
        self.setFixedWidth(620)
        self.selected_path = None

        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        self._default_location = (
            desktop if os.path.isdir(desktop) else os.path.expanduser("~")
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(10)

        title = QLabel("AGENTIC BOOTSTRAPPER IDE")
        title.setStyleSheet("color:#ffffff; font-size:16px; font-weight:bold;")
        subtitle = QLabel(
            "Pick an existing folder, or create a new project from a template "
            "in any location you choose."
        )
        subtitle.setStyleSheet("color:#9d9d9d;")
        subtitle.setWordWrap(True)

        name_label = QLabel("Project name")
        name_label.setStyleSheet("color:#9d9d9d; font-size:11px;")
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g. flask_test")

        loc_label = QLabel("Location")
        loc_label.setStyleSheet("color:#9d9d9d; font-size:11px;")
        loc_row = QHBoxLayout()
        loc_row.setSpacing(6)
        self.location_edit = QLineEdit(self._default_location)
        browse_btn = QPushButton("Browse...")
        browse_btn.setObjectName("secondary")
        browse_btn.clicked.connect(self._browse_location)
        loc_row.addWidget(self.location_edit, 1)
        loc_row.addWidget(browse_btn)

        tpl_label = QLabel("Template")
        tpl_label.setStyleSheet("color:#9d9d9d; font-size:11px;")
        self.template_combo = QComboBox()
        model = QStandardItemModel(self.template_combo)
        first_selectable = -1
        for idx, (label, value) in enumerate(TEMPLATE_CATALOG):
            item = QStandardItem(label)
            if value is None:
                item.setFlags(
                    item.flags()
                    & ~Qt.ItemFlag.ItemIsSelectable
                    & ~Qt.ItemFlag.ItemIsEnabled
                )
                item.setForeground(QColor("#6f6f6f"))
            else:
                item.setData(value, Qt.ItemDataRole.UserRole)
                if first_selectable < 0:
                    first_selectable = idx
            model.appendRow(item)
        self.template_combo.setModel(model)
        if first_selectable >= 0:
            self.template_combo.setCurrentIndex(first_selectable)

        self.path_preview = QLabel("")
        self.path_preview.setStyleSheet(
            "color:#6f6f6f; font-size:11px; padding-top:2px;"
        )
        self.path_preview.setWordWrap(True)
        self.name_edit.textChanged.connect(self._update_preview)
        self.location_edit.textChanged.connect(self._update_preview)
        self._update_preview()

        create_btn = QPushButton("Create Project")
        create_btn.clicked.connect(self._create_project)

        or_label = QLabel("— or open an existing folder —")
        or_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        or_label.setStyleSheet("color:#6f6f6f; padding:4px 0;")

        open_btn = QPushButton("Open Existing Folder...")
        open_btn.setObjectName("secondary")
        open_btn.clicked.connect(self._open_folder)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("secondary")
        cancel_btn.clicked.connect(self.reject)

        bottom = QHBoxLayout()
        bottom.addStretch(1)
        bottom.addWidget(cancel_btn)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(10)
        layout.addWidget(name_label)
        layout.addWidget(self.name_edit)
        layout.addWidget(loc_label)
        layout.addLayout(loc_row)
        layout.addWidget(tpl_label)
        layout.addWidget(self.template_combo)
        layout.addWidget(self.path_preview)
        layout.addSpacing(6)
        layout.addWidget(create_btn)
        layout.addSpacing(10)
        layout.addWidget(or_label)
        layout.addWidget(open_btn)
        layout.addSpacing(4)
        layout.addLayout(bottom)

    def _update_preview(self):
        name = sanitize_folder_name(self.name_edit.text())
        loc = self.location_edit.text().strip() or self._default_location
        if name:
            self.path_preview.setText(f"→  {os.path.join(loc, name)}")
        else:
            sep = "\\" if os.name == "nt" else "/"
            self.path_preview.setText(f"→  {loc}{sep}<project_name>")

    def _browse_location(self):
        start = self.location_edit.text().strip() or self._default_location
        if not os.path.isdir(start):
            start = os.path.expanduser("~")
        folder = QFileDialog.getExistingDirectory(
            self, "Choose where to create the project", start
        )
        if folder:
            self.location_edit.setText(folder)

    def _create_project(self):
        name = sanitize_folder_name(self.name_edit.text())
        if not name:
            QMessageBox.warning(self, "Project", "Please type a project name first.")
            return

        location = self.location_edit.text().strip() or self._default_location
        if not os.path.isdir(location):
            try:
                os.makedirs(location, exist_ok=True)
            except Exception as exc:
                QMessageBox.warning(
                    self, "Project", f"Could not use location folder:\n{exc!r}"
                )
                return

        path = os.path.join(location, name)

        if os.path.isdir(path) and os.listdir(path):
            answer = QMessageBox.question(
                self,
                "Folder Exists",
                f"{path} already exists and is not empty.\n"
                "Scaffold the selected template into it anyway? "
                "(Existing files are never overwritten.)",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return

        template = self.template_combo.currentData()
        try:
            os.makedirs(path, exist_ok=True)
            scaffold_project(path, template)
        except Exception as exc:
            QMessageBox.warning(self, "Project", f"Could not create folder:\n{exc!r}")
            return

        self.selected_path = path
        self.accept()

    def _open_folder(self):
        start = self.location_edit.text().strip() or self._default_location
        if not os.path.isdir(start):
            start = os.path.expanduser("~")
        folder = QFileDialog.getExistingDirectory(
            self, "Select Project Folder", start
        )
        if folder:
            self.selected_path = folder
            self.accept()


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self, project_dir, model, load_error=None):
        super().__init__()
        self.project_dir = project_dir
        self.model = model
        self.load_error = load_error

        self.chat_history = []
        self.chat_thread = None
        self._chat_buffer = ""
        self.runner = None
        self.venv_thread = None
        self.pip_thread = None
        self.monitor = None
        self._terminal_scroll_pending = False

        self.setWindowTitle(
            f"{os.path.basename(project_dir)} — Agentic Bootstrapper IDE (aryan)"
        )
        self.resize(1360, 840)
        self.setMinimumSize(1024, 640)

        self._build_ui()
        self._wire_shortcuts()
        self.refresh_tree()
        self._start_monitor()
        self._startup_log()
        self._auto_open_entrypoint()

        has_req = os.path.isfile(os.path.join(self.project_dir, "requirements.txt"))
        has_venv = find_venv_python(self.project_dir) is not None
        if has_req and not has_venv:
            self.log("[auto] fresh project — bootstrapping venv + dependencies...")
            QTimer.singleShot(400, self.setup_venv)
        elif has_req:
            self.log(
                "[auto] existing venv detected — click 'Install Reqs' to refresh."
            )

    # -- UI construction ----------------------------------------------------
    def _build_ui(self):
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_hud())

        main_split = QSplitter(Qt.Orientation.Horizontal)
        main_split.addWidget(self._build_sidebar())
        main_split.addWidget(self._build_editor_area())
        main_split.addWidget(self._build_chat_panel())
        main_split.setStretchFactor(0, 0)
        main_split.setStretchFactor(1, 1)
        main_split.setStretchFactor(2, 0)
        main_split.setSizes([240, 780, 340])

        vsplit = QSplitter(Qt.Orientation.Vertical)
        vsplit.addWidget(main_split)
        vsplit.addWidget(self._build_terminal())
        vsplit.setSizes([620, 200])

        root.addWidget(vsplit, 1)
        self.setCentralWidget(central)

    def _build_hud(self):
        hud = QFrame()
        hud.setObjectName("hud")
        hud.setFixedHeight(44)
        hud.setFrameShape(QFrame.Shape.NoFrame)

        lay = QHBoxLayout(hud)
        lay.setContentsMargins(12, 0, 12, 0)
        lay.setSpacing(10)

        self.project_label = QLabel(os.path.basename(self.project_dir))
        self.project_label.setStyleSheet("color:#d4d4d4; font-weight:bold;")

        self.cpu_label = QLabel("CPU --%")
        self.ram_label = QLabel("RAM --%")
        self.gpu_label = QLabel("GPU: detecting...")
        for w in (self.cpu_label, self.ram_label, self.gpu_label):
            w.setStyleSheet("color:#9d9d9d;")
            w.setMinimumWidth(90)

        self.venv_btn = QPushButton("Setup Venv")
        self.venv_btn.setObjectName("secondary")
        self.pip_btn = QPushButton("Install Reqs")
        self.pip_btn.setObjectName("secondary")
        self.run_btn = QPushButton("▶ Run Script")
        self.run_btn.setObjectName("run")
        self.stop_btn = QPushButton("■ Stop")
        self.stop_btn.setObjectName("stop")
        self.stop_btn.setEnabled(False)
        self.vscode_btn = QPushButton("Open in VS Code")

        self.venv_btn.clicked.connect(self.setup_venv)
        self.pip_btn.clicked.connect(self.install_requirements)
        self.run_btn.clicked.connect(self.run_script)
        self.stop_btn.clicked.connect(self.stop_script)
        self.vscode_btn.clicked.connect(self.open_vscode)

        lay.addWidget(self.project_label)
        lay.addStretch(1)
        lay.addWidget(self.cpu_label)
        lay.addWidget(self.ram_label)
        lay.addWidget(self.gpu_label)
        lay.addSpacing(10)
        lay.addWidget(self.venv_btn)
        lay.addWidget(self.pip_btn)
        lay.addWidget(self.run_btn)
        lay.addWidget(self.stop_btn)
        lay.addWidget(self.vscode_btn)
        return hud

    def _panel_header(self, text):
        header = QLabel(f"  {text}")
        header.setFixedHeight(26)
        header.setStyleSheet(
            "background-color:#252526; color:#9d9d9d;"
            "border-bottom:1px solid #333333; font-size:11px; letter-spacing:1px;"
        )
        return header

    def _build_sidebar(self):
        panel = QFrame()
        panel.setObjectName("panel")
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setColumnCount(1)
        self.tree.itemDoubleClicked.connect(self._tree_open)

        btn_row = QWidget()
        bl = QHBoxLayout(btn_row)
        bl.setContentsMargins(8, 8, 8, 8)
        bl.setSpacing(6)
        new_btn = QPushButton("New File")
        new_btn.setObjectName("secondary")
        ref_btn = QPushButton("Refresh")
        ref_btn.setObjectName("secondary")
        new_btn.clicked.connect(self.new_file)
        ref_btn.clicked.connect(self.refresh_tree)
        bl.addWidget(new_btn)
        bl.addWidget(ref_btn)

        lay.addWidget(self._panel_header("EXPLORER"))
        lay.addWidget(self.tree, 1)
        lay.addWidget(btn_row)
        return panel

    def _build_editor_area(self):
        self.editor_tabs = QTabWidget()
        self.editor_tabs.setTabsClosable(True)
        self.editor_tabs.setMovable(True)
        self.editor_tabs.tabCloseRequested.connect(self.close_tab)
        return self.editor_tabs

    def _build_chat_panel(self):
        panel = QFrame()
        panel.setObjectName("panel")
        panel.setMinimumWidth(300)
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self.chat_view = QTextBrowser()
        self.chat_view.setFont(QFont("Segoe UI", 10))
        self.chat_view.setOpenExternalLinks(True)

        input_row = QWidget()
        rl = QHBoxLayout(input_row)
        rl.setContentsMargins(8, 8, 8, 8)
        rl.setSpacing(6)

        self.attach_btn = QPushButton("📎")
        self.attach_btn.setObjectName("secondary")
        self.attach_btn.setCheckable(True)
        self.attach_btn.setToolTip(
            "Attach the active editor file (or selection) as context"
        )
        self.attach_btn.setFixedWidth(34)

        self.project_btn = QPushButton("📁")
        self.project_btn.setObjectName("secondary")
        self.project_btn.setCheckable(True)
        self.project_btn.setToolTip(
            "Attach the ENTIRE project tree + small files as context"
        )
        self.project_btn.setFixedWidth(34)

        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Ask the local model...")
        self.send_btn = QPushButton("Send")
        self.send_btn.setObjectName("secondary")
        rl.addWidget(self.attach_btn)
        rl.addWidget(self.project_btn)
        rl.addWidget(self.chat_input, 1)
        rl.addWidget(self.send_btn)

        self.chat_input.returnPressed.connect(self.send_chat)
        self.send_btn.clicked.connect(self.send_chat)

        lay.addWidget(self._panel_header("AI COMPANION · QWEN2.5-CODER-1.5B"))
        lay.addWidget(self.chat_view, 1)
        lay.addWidget(input_row)

        if self.model is None:
            self.chat_input.setEnabled(False)
            self.send_btn.setEnabled(False)
            self.attach_btn.setEnabled(False)
            self.project_btn.setEnabled(False)
            self.chat_input.setPlaceholderText("Model not loaded — chat disabled")
            self.chat_view.append(
                f'<span style="color:{ERROR};">AI model not loaded. '
                "See the terminal for details.</span>"
            )
        else:
            self.chat_view.append(
                '<span style="color:#858585;">Local Qwen2.5-Coder ready (n_ctx=8192). '
                "Use 📎 to attach a file, 📁 to attach the whole project.</span>"
            )
        return panel

    def _build_terminal(self):
        panel = QFrame()
        panel.setObjectName("panel")
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self.terminal = TerminalView()
        self.terminal.interrupt_requested.connect(self._on_terminal_interrupt)

        header = QLabel("  TERMINAL   ·   Ctrl+C to interrupt a running process")
        header.setFixedHeight(26)
        header.setStyleSheet(
            "background-color:#252526; color:#9d9d9d;"
            "border-bottom:1px solid #333333; font-size:11px; letter-spacing:1px;"
        )

        lay.addWidget(header)
        lay.addWidget(self.terminal, 1)
        return panel

    def _wire_shortcuts(self):
        save_action = QAction(self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save_current)
        self.addAction(save_action)

        run_action = QAction(self)
        run_action.setShortcut(QKeySequence("F5"))
        run_action.triggered.connect(self.run_script)
        self.addAction(run_action)

        stop_action = QAction(self)
        stop_action.setShortcut(QKeySequence("Shift+F5"))
        stop_action.triggered.connect(self.stop_script)
        self.addAction(stop_action)

        fullscreen_action = QAction(self)
        fullscreen_action.setShortcut(QKeySequence("F11"))
        fullscreen_action.triggered.connect(self._toggle_fullscreen)
        self.addAction(fullscreen_action)

    def _toggle_fullscreen(self):
        if self.isFullScreen():
            self.showMaximized()
        else:
            self.showFullScreen()

    # -- Startup ------------------------------------------------------------
    def _start_monitor(self):
        if psutil is None:
            self.log("[vitals] psutil is not installed — HUD will show n/a.")
        self.monitor = HardwareMonitorThread()
        self.monitor.vitals.connect(self._on_vitals)
        self.monitor.start()

    def _startup_log(self):
        self.log("Agentic Bootstrapper IDE ready.")
        self.log(f"[workspace] {self.project_dir}")
        if getattr(sys, "frozen", False):
            py = find_system_python()
            if py:
                self.log(f"[frozen] system Python: {py}")
            else:
                self.log(
                    "[frozen] WARNING: no system Python — "
                    "venv and Run features will not work."
                )
        venv_py = find_venv_python(self.project_dir)
        if venv_py:
            self.log(f"[venv] detected: {venv_py}")
        else:
            self.log("[venv] no .venv yet — Setup Venv or wait for auto-bootstrap.")
        if self.model is not None:
            self.log(
                "[model] Qwen2.5-Coder 1.5B (Q4_K_M) loaded — n_ctx=8192, n_threads=4."
            )
        else:
            self.log("[model] not loaded: " + (self.load_error or "unknown error"))
            self.log("[model] AI chat is disabled until the model is available.")

    def _auto_open_entrypoint(self):
        candidates = (
            "app.py",
            "main.py",
            "cli.py",
            "analysis.py",
            "scraper.py",
            "test_sample.py",
            "README.md",
            "manage.py",
        )
        for name in candidates:
            path = os.path.join(self.project_dir, name)
            if os.path.isfile(path):
                self.open_file(path)
                return

    # -- Hardware HUD -------------------------------------------------------
    def _on_vitals(self, cpu, ram, gpu):
        try:
            if cpu < 0:
                self.cpu_label.setText("CPU n/a")
                self.ram_label.setText("RAM n/a")
                self.cpu_label.setStyleSheet("color:#6f6f6f;")
                self.ram_label.setStyleSheet("color:#6f6f6f;")
            else:
                self.cpu_label.setText(f"CPU {cpu:0.0f}%")
                self.ram_label.setText(f"RAM {ram:0.0f}%")
                self.cpu_label.setStyleSheet(
                    f"color:{ERROR};" if cpu >= 85 else "color:#9d9d9d;"
                )
                self.ram_label.setStyleSheet(
                    f"color:{ERROR};" if ram >= 85 else "color:#9d9d9d;"
                )
            self.gpu_label.setText(f"GPU: {gpu}")
            self.gpu_label.setToolTip(gpu)
        except Exception:
            pass

    # -- Terminal / logging -------------------------------------------------
    def log(self, text):
        try:
            self.terminal.appendPlainText(str(text))
            if not self._terminal_scroll_pending:
                self._terminal_scroll_pending = True
                QTimer.singleShot(40, self._flush_terminal_scroll)
        except Exception:
            pass

    def _flush_terminal_scroll(self):
        self._terminal_scroll_pending = False
        try:
            sb = self.terminal.verticalScrollBar()
            sb.setValue(sb.maximum())
        except Exception:
            pass

    # -- File explorer ------------------------------------------------------
    def refresh_tree(self):
        self.tree.clear()
        root = QTreeWidgetItem([os.path.basename(self.project_dir) or self.project_dir])
        root.setData(0, Qt.ItemDataRole.UserRole, self.project_dir)
        self.tree.addTopLevelItem(root)
        self._populate_tree(root, self.project_dir, 0)
        root.setExpanded(True)

    def _populate_tree(self, parent_item, path, depth):
        if depth > 5:
            return
        try:
            entries = sorted(os.listdir(path))
        except Exception:
            return

        dirs = [
            e for e in entries
            if os.path.isdir(os.path.join(path, e)) and e not in SKIP_DIRS
        ]
        files = [e for e in entries if os.path.isfile(os.path.join(path, e))]

        for d in dirs:
            full = os.path.join(path, d)
            item = QTreeWidgetItem([d])
            item.setData(0, Qt.ItemDataRole.UserRole, full)
            parent_item.addChild(item)
            self._populate_tree(item, full, depth + 1)

        for f in files:
            full = os.path.join(path, f)
            item = QTreeWidgetItem([f])
            item.setData(0, Qt.ItemDataRole.UserRole, full)
            parent_item.addChild(item)

    def _tree_open(self, item, _column):
        if item is None:
            return
        path = item.data(0, Qt.ItemDataRole.UserRole)
        if path and os.path.isfile(path):
            self.open_file(path)

    # -- Editor tabs --------------------------------------------------------
    def open_file(self, path):
        for i in range(self.editor_tabs.count()):
            widget = self.editor_tabs.widget(i)
            if getattr(widget, "file_path", None) == path:
                self.editor_tabs.setCurrentIndex(i)
                return
        try:
            if os.path.getsize(path) > 2 * 1024 * 1024:
                self.log(f"[file] {path} is larger than 2 MB — not opened.")
                return
            with open(path, "r", encoding="utf-8", errors="replace") as handle:
                text = handle.read()
        except Exception as exc:
            self.log(f"[file] cannot open {path}: {exc!r}")
            return

        editor = CodeEditor()
        editor.file_path = path
        editor.setPlainText(text)
        editor.document().setModified(False)
        index = self.editor_tabs.addTab(editor, os.path.basename(path))
        self.editor_tabs.setCurrentIndex(index)
        self.log(f"[file] opened {path}")

    def new_file(self):
        editor = CodeEditor()
        editor.file_path = None
        index = self.editor_tabs.addTab(editor, "untitled")
        self.editor_tabs.setCurrentIndex(index)
        editor.setFocus()

    def save_current(self):
        editor = self.editor_tabs.currentWidget()
        if editor is not None:
            self.save_editor(editor)

    def save_editor(self, editor):
        path = getattr(editor, "file_path", None)
        if not path:
            path, _ = QFileDialog.getSaveFileName(
                self, "Save File", self.project_dir,
                "Python Files (*.py);;All Files (*)"
            )
            if not path:
                return False
            editor.file_path = path
        try:
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(editor.toPlainText())
            editor.document().setModified(False)
            index = self.editor_tabs.indexOf(editor)
            if index >= 0:
                self.editor_tabs.setTabText(index, os.path.basename(path))
            self.log(f"[file] saved {path}")
            self.refresh_tree()
            return True
        except Exception as exc:
            self.log(f"[file] save failed: {exc!r}")
            QMessageBox.warning(self, "Save", f"Could not save file:\n{exc!r}")
            return False

    def close_tab(self, index):
        editor = self.editor_tabs.widget(index)
        if editor is None:
            return
        if editor.document().isModified():
            answer = QMessageBox.question(
                self,
                "Unsaved Changes",
                f"'{self.editor_tabs.tabText(index)}' has unsaved changes.\n"
                "Save before closing?",
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel,
            )
            if answer == QMessageBox.StandardButton.Save:
                if not self.save_editor(editor):
                    return
            elif answer == QMessageBox.StandardButton.Cancel:
                return
        self.editor_tabs.removeTab(index)

    # -- Hardware guardrail -------------------------------------------------
    def _detect_ml_keywords(self, code):
        hits = []
        for pattern, label in ML_PATTERNS:
            if re.search(pattern, code, re.IGNORECASE):
                hits.append(label)
        return hits

    def _confirm_ml_run(self, hits):
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Warning)
        box.setWindowTitle("Hardware Guardrail")
        box.setText("Heavy ML/DL code detected in the active editor.")
        box.setInformativeText(
            "Detected: " + ", ".join(hits) + "\n\n"
            'Hardware profile "aryan":\n'
            "• CPU: Intel Core i5, 4 cores — training will saturate every core\n"
            "• RAM: 8 GB — large models or batches may swap or OOM\n"
            "• GPU: integrated Intel UHD only — no CUDA acceleration\n\n"
            "Suggestions: use CPU wheels, small batch sizes, quantized models, "
            "and prefer inference over training.\n\n"
            "Run anyway?"
        )
        abort_btn = box.addButton("Abort", QMessageBox.ButtonRole.RejectRole)
        box.addButton("Proceed Anyway", QMessageBox.ButtonRole.AcceptRole)
        box.setDefaultButton(abort_btn)
        box.exec()
        return box.clickedButton() is not abort_btn

    # -- Run pipeline -------------------------------------------------------
    def run_script(self):
        editor = self.editor_tabs.currentWidget()
        if editor is None:
            QMessageBox.information(self, "Run", "Open a Python file in the editor first.")
            return
        if self.runner is not None and self.runner.isRunning():
            self.log("[run] a script is already running.")
            return

        code = editor.toPlainText()
        hits = self._detect_ml_keywords(code)
        if hits and not self._confirm_ml_run(hits):
            self.log("[guardrail] run aborted by user.")
            return

        path = getattr(editor, "file_path", None)
        if path is None:
            self.log("[run] file has no path yet — save it first (Ctrl+S).")
            return

        try:
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(code)
            editor.document().setModified(False)
        except Exception as exc:
            self.log(f"[run] failed to save before running: {exc!r}")
            return

        python_exe = (
            find_venv_python(self.project_dir)
            or find_system_python()
            or sys.executable
        )
        self.log("")
        self.log(f"[run] {os.path.basename(path)}")
        self.log(f"[run] interpreter: {python_exe}")

        self.run_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.runner = ScriptRunnerThread(python_exe, path, self.project_dir)
        self.runner.output.connect(self.log)
        self.runner.run_finished.connect(self._on_run_finished)
        self.runner.start()

    def _on_run_finished(self, code):
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.log(f"[run] process exited with code {code}")

    def stop_script(self):
        if self.runner is None or not self.runner.isRunning():
            return
        self.log("[run] stopping process tree...")
        self.run_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.runner.stop()

    def _on_terminal_interrupt(self):
        if self.runner is None or not self.runner.isRunning():
            return
        self.log("^C")
        self.stop_script()

    # -- Venv pipeline ------------------------------------------------------
    def setup_venv(self):
        if self.venv_thread is not None and self.venv_thread.isRunning():
            self.log("[venv] setup already running.")
            return
        py = find_system_python()
        if py is None:
            self.log("[venv] no system Python found — install Python from python.org")
            QMessageBox.warning(
                self, "Setup Venv",
                "No system Python interpreter was found.\n"
                "Install Python from python.org and ensure it's on PATH."
            )
            return
        self.log("")
        self.log(f"[venv] starting environment pipeline with base interpreter: {py}")
        self.run_btn.setEnabled(False)
        self.venv_btn.setEnabled(False)
        self.venv_thread = VenvSetupThread(py, self.project_dir)
        self.venv_thread.output.connect(self.log)
        self.venv_thread.setup_finished.connect(self._on_venv_finished)
        self.venv_thread.start()

    def _on_venv_finished(self, ok, message):
        self.venv_btn.setEnabled(True)
        if not ok:
            self.run_btn.setEnabled(True)
            self.log(f"[venv] failed: {message}")
            return

        self.log(f"[venv] ready: {message}")

        req = os.path.join(self.project_dir, "requirements.txt")
        if os.path.isfile(req):
            self.log("[venv] requirements.txt found — installing dependencies...")
            self.install_requirements()
        else:
            self.run_btn.setEnabled(True)
            self.log("[venv] no requirements.txt — skipping package install.")

    # -- Pip pipeline -------------------------------------------------------
    def install_requirements(self):
        if self.pip_thread is not None and self.pip_thread.isRunning():
            self.log("[pip] install already running.")
            return

        vpy = find_venv_python(self.project_dir)
        if not vpy:
            QMessageBox.information(
                self, "Install Reqs",
                "No .venv found. Click 'Setup Venv' first."
            )
            return
        if not os.path.isfile(os.path.join(self.project_dir, "requirements.txt")):
            self.log("[pip] no requirements.txt in this project — nothing to install.")
            return

        self.log("")
        self.log("[pip] installing requirements into .venv ...")
        self.pip_btn.setEnabled(False)
        self.run_btn.setEnabled(False)
        self.pip_thread = PipInstallThread(vpy, self.project_dir)
        self.pip_thread.output.connect(self.log)
        self.pip_thread.install_finished.connect(self._on_pip_finished)
        self.pip_thread.start()

    def _on_pip_finished(self, ok, message):
        self.pip_btn.setEnabled(True)
        self.run_btn.setEnabled(True)
        if ok:
            self.log(f"[pip] {message}")
        else:
            self.log(f"[pip] failed: {message}")

    # -- VS Code hand-off ---------------------------------------------------
    def open_vscode(self):
        path = self.project_dir
        code_cmd = shutil.which("code") or shutil.which("code.cmd")
        try:
            if code_cmd:
                subprocess.Popen([code_cmd, path])
            elif os.name == "nt":
                subprocess.Popen(
                    ["cmd", "/c", "code", path],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
            else:
                subprocess.Popen(["code", path])
            self.log(f"[vscode] opening {path} in VS Code ...")
        except Exception as exc:
            self.log(f"[vscode] failed: {exc!r}")
            QMessageBox.warning(
                self,
                "VS Code",
                "Could not launch VS Code.\n"
                "Make sure the 'code' command is available on your PATH.\n\n"
                f"{exc!r}",
            )

    # -- AI companion chat --------------------------------------------------
    def _chat_scroll_bottom(self):
        sb = self.chat_view.verticalScrollBar()
        sb.setValue(sb.maximum())

    def send_chat(self):
        if self.model is None:
            self.log("[chat] model not loaded — chat unavailable.")
            return
        if self.chat_thread is not None and self.chat_thread.isRunning():
            return
        text = self.chat_input.text().strip()
        if not text:
            return

        self.chat_input.clear()

        payload = text
        attached_file = False
        attached_project = False

        if self.project_btn.isChecked():
            bundle, stats = build_project_context(self.project_dir)
            payload = f"{bundle}\n\n{text}"
            attached_project = True
            self.project_btn.setChecked(False)
            self.log(
                f"[chat] project context: {stats['files_included']} files, "
                f"{stats['files_skipped']} skipped, "
                f"~{stats['est_tokens']} tokens"
            )
            if stats["est_tokens"] > 6500:
                self.log(
                    "[chat] warning: project context is large — "
                    "if the answer gets truncated, try 📎 on specific files."
                )

        elif self.attach_btn.isChecked():
            editor = self.editor_tabs.currentWidget()
            ctx = build_editor_context(editor)
            if ctx:
                payload = f"{ctx}\n\n{text}"
                attached_file = True
            self.attach_btn.setChecked(False)

        self.chat_history.append({"role": "user", "content": payload})
        if len(self.chat_history) > 24:
            self.chat_history = self.chat_history[-24:]

        safe = html.escape(text).replace("\n", "<br>")
        self.chat_view.append(
            f'<span style="color:#4ec9b0; font-weight:bold;">You:</span> {safe}'
        )
        if attached_project:
            self.chat_view.append(
                '<span style="color:#6f6f6f;">[📁 project attached]</span>'
            )
        elif attached_file:
            self.chat_view.append(
                '<span style="color:#6f6f6f;">[📎 active file attached]</span>'
            )
        self.chat_view.append(
            '<span style="color:#0e639c; font-weight:bold;">Qwen:</span> '
        )
        self._chat_scroll_bottom()

        self._chat_buffer = ""
        self.chat_input.setEnabled(False)
        self.send_btn.setEnabled(False)
        self.attach_btn.setEnabled(False)
        self.project_btn.setEnabled(False)

        history = list(self.chat_history[-10:])
        self.chat_thread = ChatThread(self.model, SYSTEM_PROMPT, history)
        self.chat_thread.token.connect(self._on_chat_token)
        self.chat_thread.error.connect(self._on_chat_error)
        self.chat_thread.chat_done.connect(self._on_chat_done)
        self.chat_thread.start()

    def _on_chat_token(self, token):
        self._chat_buffer += token
        self.chat_view.moveCursor(QTextCursor.MoveOperation.End)
        self.chat_view.insertPlainText(token)
        self._chat_scroll_bottom()

    def _on_chat_error(self, message):
        self.log(f"[chat] error: {message}")
        self.chat_view.moveCursor(QTextCursor.MoveOperation.End)
        self.chat_view.insertPlainText(f"\n[error] {message}")
        self._chat_scroll_bottom()

    def _on_chat_done(self):
        if self._chat_buffer.strip():
            self.chat_history.append(
                {"role": "assistant", "content": self._chat_buffer}
            )
        self._chat_buffer = ""
        self.chat_view.moveCursor(QTextCursor.MoveOperation.End)
        self.chat_view.insertPlainText("\n")
        self._chat_scroll_bottom()
        self.chat_input.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.attach_btn.setEnabled(True)
        self.project_btn.setEnabled(True)
        self.chat_input.setFocus()

    # -- Shutdown -----------------------------------------------------------
    def closeEvent(self, event):
        try:
            if self.monitor is not None:
                self.monitor.stop()
                self.monitor.wait(2000)
        except Exception:
            pass
        try:
            if self.runner is not None and self.runner.isRunning():
                self.runner.stop()
                self.runner.wait(3000)
        except Exception:
            pass
        try:
            if self.venv_thread is not None and self.venv_thread.isRunning():
                self.venv_thread.wait(1000)
        except Exception:
            pass
        try:
            if self.pip_thread is not None and self.pip_thread.isRunning():
                self.pip_thread.wait(1000)
        except Exception:
            pass
        try:
            if self.chat_thread is not None and self.chat_thread.isRunning():
                self.chat_thread.wait(1500)
        except Exception:
            pass
        event.accept()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def _main_impl():
    app = QApplication(sys.argv)
    app.setApplicationName("Agentic Bootstrapper IDE")
    app.setFont(QFont("Segoe UI", 9))
    app.setStyleSheet(STYLESHEET)
    app.setQuitOnLastWindowClosed(False)

    splash = SplashScreen()
    splash.show()
    QApplication.processEvents()

    model_path = resolve_model_path()
    loader = ModelLoaderThread(model_path)
    state = {"model": None, "error": None, "done": False}

    def finish():
        if state["done"]:
            return
        state["done"] = True
        splash.set_message("Ready.")
        QTimer.singleShot(250, proceed)

    def proceed():
        splash.close()
        selector = ProjectSelector()
        if selector.exec() != QDialog.DialogCode.Accepted or not selector.selected_path:
            app.quit()
            return
        window = MainWindow(selector.selected_path, state["model"], state["error"])
        window.showMaximized()
        app._main_window = window
        app._loader = loader
        app.setQuitOnLastWindowClosed(True)

    loader.progress.connect(splash.set_message)
    loader.loaded.connect(lambda m: (state.__setitem__("model", m), finish()))
    loader.failed.connect(lambda e: (state.__setitem__("error", e), finish()))
    loader.start()

    sys.exit(app.exec())


def main():
    try:
        _main_impl()
    except Exception:
        tb = traceback.format_exc()
        try:
            _a = QApplication.instance() or QApplication(sys.argv)
            QMessageBox.critical(None, "Startup Error", tb)
        except Exception:
            pass
        try:
            base = (os.path.dirname(sys.executable)
                    if getattr(sys, "frozen", False)
                    else os.path.dirname(os.path.abspath(__file__)))
            with open(os.path.join(base, "ai_ide_crash.log"), "w",
                      encoding="utf-8") as f:
                f.write(tb)
        except Exception:
            pass
        raise


if __name__ == "__main__":
    main()