"""Launcher script for School Comms Aggregator - builds to .exe for taskbar pinning."""
import os
import sys

# Determine the app directory
if getattr(sys, 'frozen', False):
    # Running as PyInstaller bundle - use fixed path to project
    app_dir = r"C:\Users\jerem\school-comms-aggregator"
    venv_dir = os.path.join(app_dir, ".venv")

    # Set up Playwright browser path (installed in AppData\Local\ms-playwright)
    local_app_data = os.environ.get("LOCALAPPDATA", r"C:\Users\jerem\AppData\Local")
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = os.path.join(local_app_data, "ms-playwright")

    # Add venv site-packages to path so playwright can find its driver
    site_packages = os.path.join(venv_dir, "Lib", "site-packages")
    if site_packages not in sys.path:
        sys.path.insert(0, site_packages)
else:
    # Running as script
    app_dir = os.path.dirname(os.path.abspath(__file__))

# Set up the path
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

os.chdir(app_dir)
os.environ["PYTHONPATH"] = app_dir

# Launch the main app
from src.main import main
main()
