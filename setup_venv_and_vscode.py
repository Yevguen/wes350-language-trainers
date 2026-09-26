import os
import json
import subprocess
from pathlib import Path

# Project base
project_root = Path(__file__).resolve().parent
venv_path = project_root / ".venv"
vscode_settings_dir = project_root / ".vscode"
vscode_settings_file = vscode_settings_dir / "settings.json"

# 1. Create virtual environment if not present
if not venv_path.exists():
    print("Creating virtual environment...")
    subprocess.run(["python", "-m", "venv", str(venv_path)])
else:
    print("Virtual environment already exists.")

# 2. Determine the interpreter path
interpreter_path = str(venv_path / "Scripts" / "python.exe")

# 3. Create .vscode/settings.json with auto-activation
print("Configuring VS Code to use .venv...")

vscode_settings_dir.mkdir(exist_ok=True)

settings = {
    "python.defaultInterpreterPath": interpreter_path,
    "python.terminal.activateEnvironment": True
}

# Merge with existing settings if present
if vscode_settings_file.exists():
    with open(vscode_settings_file, "r") as f:
        existing = json.load(f)
    existing.update(settings)
    settings = existing

# Write the settings
with open(vscode_settings_file, "w") as f:
    json.dump(settings, f, indent=4)

print(f"✅ VS Code Python interpreter set to: {interpreter_path}")
