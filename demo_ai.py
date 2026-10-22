#!/usr/bin/env python3
"""
Launcher para la demostración interactiva del Asistente IA de Nexus Digital Store.
"""
#!/usr/bin/env python3
"""
Launcher para la demostración interactiva del Asistente IA de Nexus Digital Store.
"""
import os
import subprocess
import sys

backend_dir = os.path.join(os.path.dirname(__file__), "nexus-backend")
script_path = os.path.join(backend_dir, "demo_llm.py")

if not os.path.exists(script_path):
    print(f"Error: No se encontró {script_path}")
    sys.exit(1)

# Usar el python del virtualenv si existe y es ejecutable, sino sys.executable
venv_python = os.path.join(backend_dir, ".venv", "bin", "python")
python_exec = sys.executable
if os.path.exists(venv_python) and os.access(venv_python, os.X_OK):
    python_exec = venv_python

args = [python_exec, script_path] + sys.argv[1:]
env = os.environ.copy()
env["PYTHONPATH"] = os.path.join(backend_dir, "src")

try:
    sys.exit(subprocess.call(args, env=env))
except Exception:
    os.execv(python_exec, args)

