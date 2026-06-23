import os
import sys

# Set default command line arguments to "runserver" with a specific port if none are provided
if __name__ == '__main__':
    if len(sys.argv) == 1:
        # If double-clicked without arguments, default to running the server
        sys.argv.append('runserver')
        sys.argv.append('127.0.0.1:8000')
        sys.argv.append('--noreload') # Required to avoid multiprocess restarting issues in PyInstaller

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shade_project.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    
    # Optional: Automatically open browser
    if 'runserver' in sys.argv:
        import threading
        import webbrowser
        import time
        
        def open_browser():
            time.sleep(2)
            webbrowser.open('http://127.0.0.1:8000/login/')
            
        threading.Thread(target=open_browser, daemon=True).start()

    execute_from_command_line(sys.argv)
