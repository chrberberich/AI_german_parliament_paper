from pathlib import Path
import subprocess
import shutil
import sys


BASE = Path(__file__).parent  
qmd = qmd = Path(__file__).resolve().parents[2] / "AI_parliament_paper" / "AI_parliament.qmd"

# grab quarto

if shutil.which("quarto") is None:
    sys.exit("Quarto not found. Please install it. If already installed, make sure it's in your PATH.")

quarto_path = shutil.which("quarto")
subprocess.run([quarto_path, "render", str(qmd)], check=True)

