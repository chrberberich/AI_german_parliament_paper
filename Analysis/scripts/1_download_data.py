"""
download_data.py
----------------
Downloads and extracts the Zenodo dataset (CPP-BT 2026-01-17).
"""

import os
import sys
import zipfile
import requests
import nltk

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DOWNLOAD_URL = "https://zenodo.org/records/18177196/files/CPP-BT_2026-01-17_DE_CSV_Reden_Gesamt.zip?download=1"
ZIP_FILENAME  = "CPP-BT_2026-01-17_DE_CSV_Reden_Gesamt.zip"
DATA_DIR      = "./data"
ZIP_PATH      = os.path.join(DATA_DIR, ZIP_FILENAME)
TARGET_FILE   = os.path.join(DATA_DIR, "CPP-BT_2026-01-17_DE_CSV_Reden_Gesamt.csv")

# download stopwords if not available
try:
    from nltk.corpus import stopwords
    stopwords.words("german")
except LookupError:
    user_input = input("Stopword-list not found. Download? (y/n): ")
    if user_input.lower() == "y":
        nltk.download("stopwords")


def dataset_exists() -> bool:
    return os.path.exists(TARGET_FILE)


def ask_user_confirmation(prompt: str) -> bool:
    """Prompts the user with y/n. Repeats on invalid input."""
    while True:
        answer = input(prompt).strip().lower()
        if answer in ("y", "n"):
            return answer == "y"
        print("  Please answer with 'y' or 'n'.")


def download_and_extract() -> None:
    """Downloads the ZIP file and extracts it."""
    os.makedirs(DATA_DIR, exist_ok=True)

    # Download
    print(f"  Downloading: {ZIP_FILENAME} ...", end=" ", flush=True)
    response = requests.get(DOWNLOAD_URL, stream=True, timeout=120)
    response.raise_for_status()
    with open(ZIP_PATH, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    print("done.")

    # Extract
    print(f"  Extracting to {DATA_DIR}/ ...", end=" ", flush=True)
    with zipfile.ZipFile(ZIP_PATH, "r") as zf:
        zf.extractall(DATA_DIR)
    print("done.")

    # Clean up ZIP
    os.remove(ZIP_PATH)
    print("  ZIP file deleted.")


def main():
    print("Dataset: CPP-BT 2026-01-17")
    print(f"Local directory: {os.path.abspath(DATA_DIR)}\n")

    if dataset_exists():
        print("✓ Dataset already exists locally.")
        return

    print("Dataset not found.\n")
    if ask_user_confirmation("Download and extract dataset? [y/n]: "):
        print()
        try:
            download_and_extract()
            print("\n✓ Dataset ready.")
        except requests.RequestException as e:
            print(f"\nDownload error: {e}")
            sys.exit(1)
        except zipfile.BadZipFile as e:
            print(f"\nExtraction error: {e}")
            sys.exit(1)
    else:
        print("Aborted.")
        sys.exit(0)


if __name__ == "__main__":
    main()