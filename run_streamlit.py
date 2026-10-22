#!/usr/bin/env python3
"""Launcher para ejecutar la aplicación de Streamlit de Nexus AI."""

import os
import subprocess
import sys

root_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(root_dir, "nexus-backend")
app_path = os.path.join(root_dir, "nexus-ai", "app.py")

venv_streamlit = os.path.join(backend_dir, ".venv", "bin", "streamlit")

if os.path.exists(venv_streamlit) and os.access(venv_streamlit, os.X_OK):
    cmd = [venv_streamlit, "run", app_path] + sys.argv[1:]
else:
    venv_python = os.path.join(backend_dir, ".venv", "bin", "python")
    python_exec = venv_python if os.path.exists(venv_python) else sys.executable
    cmd = [python_exec, "-m", "streamlit", "run", app_path] + sys.argv[1:]

env = os.environ.copy()
env["PYTHONPATH"] = os.path.join(backend_dir, "src")

print(f"🚀 Iniciando Nexus AI Streamlit Lab en http://localhost:8501 ...")
sys.exit(subprocess.call(cmd, env=env))

