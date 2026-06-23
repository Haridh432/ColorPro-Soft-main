import os
import shutil
import subprocess
import sys

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(root_dir, 'backend')
    frontend_dir = os.path.join(root_dir, 'frontend')

    print("================================================")
    print(" COLORPRO WINDOWS PACKAGE BUILDER")
    print("================================================")
    
    # Find the correct python executable (checking venv first)
    venv_python = os.path.join(backend_dir, 'venv', 'Scripts', 'python.exe')
    if not os.path.exists(venv_python):
        venv_python = os.path.join(backend_dir, 'venv', 'bin', 'python')
        
    python_exe = venv_python if os.path.exists(venv_python) else sys.executable

    print("\n[1/4] Installing necessary Python packages into the environment...")
    subprocess.check_call([python_exe, "-m", "pip", "install", "pyinstaller", "whitenoise", "-r", "requirements.txt"], cwd=backend_dir)

    # 2. Build the Next.js Frontend
    print("\n[2/4] Compiling Next.js Dashboard to Static HTML...")
    # Using npm.cmd instead of npm to avoid Windows shell execution issues
    npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
    subprocess.check_call([npm_cmd, "run", "build"], cwd=frontend_dir)

    # 3. Copy compiled frontend into django
    print("\n[3/4] Copying compiled frontend to backend static directory...")
    frontend_out = os.path.join(frontend_dir, 'out')
    backend_dest = os.path.join(backend_dir, 'frontend_build')
    
    if os.path.exists(backend_dest):
        shutil.rmtree(backend_dest)
        
    shutil.copytree(frontend_out, backend_dest)

    # 4. Run PyInstaller
    print("\n[4/4] Packaging entire application to a standalone Windows App (.exe)...")
    
    separator = ";" if os.name == "nt" else ":"
    pyinstaller_cmd = [
        python_exe, "-m", "PyInstaller",
        "--noconfirm",
        "--name", "ColorPro_Server",
        "--onedir", # Creates a folder instead of a single massive and slow exe
        "--add-data", f"frontend_build{separator}frontend_build",
        "--add-data", f"db.sqlite3{separator}.", # Include existing DB if they want
        "--hidden-import", "whitenoise",
        "--hidden-import", "scipy.special.cython_special",  # Often needed by scikit/numpy
        "windows_entry.py"
    ]
    
    subprocess.check_call(pyinstaller_cmd, cwd=backend_dir)

    print("\n================================================")
    print(" BUILD COMPLETE!")
    print(f"Your application has been packaged successfully.")
    print(f"You can find your packaged Windows App inside:")
    print(f" {os.path.join(backend_dir, 'dist', 'ColorPro_Server')}")
    print("You can zip this folder and send it to any Windows computer!")
    print("To start the app, simply double-click ColorPro_Server.exe")
    print("================================================")

if __name__ == "__main__":
    main()
