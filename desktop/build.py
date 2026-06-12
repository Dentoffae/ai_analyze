"""
Скрипт сборки .exe файла для Windows
"""
import subprocess
import sys
from pathlib import Path


def build_exe():
    print("=" * 60)
    print("BUILDING DESKTOP APPLICATION")
    print("=" * 60)

    current_dir = Path(__file__).parent
    app_name = "CompetitorMonitor"

    try:
        import PyInstaller

        print(f"\nPyInstaller {PyInstaller.__version__}")
    except ImportError:
        print("\nPyInstaller is not installed. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        import PyInstaller

        print(f"PyInstaller {PyInstaller.__version__}")

    pyinstaller_args = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name",
        app_name,
        "--onefile",
        "--windowed",
        "--noconfirm",
        "--clean",
        "--collect-all",
        "PyQt6",
        "--hidden-import",
        "requests",
        "main.py",
    ]

    print(f"\nBuilding: {app_name}.exe")
    print("-" * 60)

    result = subprocess.run(pyinstaller_args, cwd=current_dir)

    exe_path = current_dir / "dist" / f"{app_name}.exe"
    if result.returncode == 0 and exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print("\n" + "=" * 60)
        print("BUILD SUCCESSFUL")
        print("=" * 60)
        print(f"\nOutput: {exe_path}")
        print(f"Size: {size_mb:.1f} MB")
        print("\nStart backend before running the exe:")
        print("  python run.py")
    else:
        print("\nBuild failed")
        sys.exit(1)


if __name__ == "__main__":
    build_exe()
