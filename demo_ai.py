#!/usr/bin/env python3
"""
Launcher para la demostración interactiva del Asistente IA de Nexus Digital Store.
"""
import os
import sys

# Ejecutar el script demo en nexus-backend
backend_dir = os.path.join(os.path.dirname(__file__), "nexus-backend")
script_path = os.path.join(backend_dir, "demo_llm.py")

if not os.path.exists(script_path):
    print(f"Error: No se encontró {script_path}")
    sys.exit(1)

# Usar el python del virtualenv si existe, sino el python actual
venv_python = os.path.join(backend_dir, ".venv", "bin", "python")
python_exec = venv_python if os.path.exists(venv_python) else sys.executable

args = [python_exec, script_path] + sys.argv[1:]
os.environ["PYTHONPATH"] = os.path.join(backend_dir, "src")
os.execv(python_exec, args)

