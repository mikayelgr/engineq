import os
import platform
import subprocess
import sys
import requests
import zipfile
import tarfile
import io
import stat
from dotenv import load_dotenv

DBMATE_VERSION = "v2.27.0" # Specify the desired dbmate version

# Correctly determine directories relative to this script file
# acura/scripts/run_dbmate_cli.py
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# acura/
ACURA_DIR = os.path.join(SCRIPT_DIR, "..")
# <project_root>/ (assuming acura is a top-level dir in the project)
PROJECT_ROOT = os.path.join(ACURA_DIR, "..")
# <project_root>/migrator/
MIGRATOR_DIR = os.path.join(PROJECT_ROOT, "migrator")
# <project_root>/migrator/bin/
BIN_DIR = os.path.join(MIGRATOR_DIR, "bin")

DBMATE_EXE_NAME = "dbmate.exe" if platform.system().lower() == "windows" else "dbmate"
DBMATE_PATH = os.path.join(BIN_DIR, DBMATE_EXE_NAME)

def get_asset_details():
    system = platform.system().lower()
    machine = platform.machine().lower()
    asset_filename = None
    is_compressed = False
    exe_name_in_archive = DBMATE_EXE_NAME

    if system == "linux":
        if machine in ["x86_64", "amd64"]:
            asset_filename = "dbmate-linux-amd64"
        elif machine in ["aarch64", "arm64"]:
            asset_filename = "dbmate-linux-arm64"
    elif system == "darwin":
        if machine in ["x86_64", "amd64"]:
            asset_filename = "dbmate-macos-amd64"
        elif machine == "arm64":
            asset_filename = "dbmate-macos-arm64"
    elif system == "windows":
        if machine in ["x86_64", "amd64"]:
            asset_filename = "dbmate-windows-amd64.zip"
            is_compressed = True

    if not asset_filename:
        print(f"Error: Unsupported OS/architecture: {system}/{machine}", file=sys.stderr)
        sys.exit(1)

    url = f"https://github.com/amacneil/dbmate/releases/download/{DBMATE_VERSION}/{asset_filename}"
    return asset_filename, url, is_compressed, exe_name_in_archive

def download_and_extract(asset_filename, url, is_compressed, exe_name_in_archive):
    print(f"Downloading dbmate from {url}...")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        os.makedirs(BIN_DIR, exist_ok=True)

        if is_compressed:
            if asset_filename.endswith(".zip"):
                with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                    # Try to find the exe name; some zips might have a folder
                    member_to_extract = None
                    for member in z.namelist():
                        if member.endswith(exe_name_in_archive):
                            member_to_extract = member
                            break
                    if member_to_extract:
                        z.extract(member_to_extract, path=BIN_DIR)
                        # Rename if extracted into a subdirectory within BIN_DIR
                        extracted_file_path = os.path.join(BIN_DIR, member_to_extract)
                        if os.path.dirname(member_to_extract): # It was in a subfolder
                            os.rename(extracted_file_path, DBMATE_PATH)
                            # Clean up empty subfolder if possible
                            try:
                                os.rmdir(os.path.join(BIN_DIR, os.path.dirname(member_to_extract)))
                            except OSError:
                                pass # Not empty or error
                        # If not in subfolder, it should already be at DBMATE_PATH if exe_name_in_archive matches DBMATE_EXE_NAME
                    else:
                        raise Exception(f"{exe_name_in_archive} not found in zip.")
            # Add .tar.gz handling if necessary based on actual assets
            # elif asset_filename.endswith(".tar.gz"): ...
            else:
                raise Exception(f"Unsupported archive format: {asset_filename}")
        else:
            with open(DBMATE_PATH, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

        current_st = os.stat(DBMATE_PATH)
        os.chmod(DBMATE_PATH, current_st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
        print(f"dbmate installed/updated successfully at {DBMATE_PATH}")

    except requests.exceptions.RequestException as e:
        print(f"Error downloading dbmate: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error processing dbmate archive: {e}", file=sys.stderr)
        sys.exit(1)

def ensure_dbmate_available():
    if not os.path.exists(DBMATE_PATH):
        print(f"dbmate not found at {DBMATE_PATH}. Attempting to download...")
        asset_filename, url, is_compressed, exe_name_in_archive = get_asset_details()
        download_and_extract(asset_filename, url, is_compressed, exe_name_in_archive)
    else:
        print(f"dbmate already exists at {DBMATE_PATH}")
        # Version check functionality can be implemented here if needed in the future.


def main():
    ensure_dbmate_available()

    # Migrations directory is relative to PROJECT_ROOT
    migrations_dir = os.path.join(PROJECT_ROOT, "migrations")

    # Load .env from migrator directory for DATABASE_URL
    dotenv_path = os.path.join(MIGRATOR_DIR, '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path=dotenv_path)
        # print(f"Loaded environment variables from {dotenv_path}")

    db_url_env = os.getenv("DATABASE_URL")
    # If DATABASE_URL is not set, dbmate will try to use its default (e.g. from .env file in current dir or specific envs)
    # We must ensure dbmate knows where the migrations are.

    command_args = ["-d", migrations_dir]

    # If DATABASE_URL is explicitly found, prefer passing it via --url to avoid ambiguity
    if db_url_env:
        command_args.extend(["--url", db_url_env])

    command = [DBMATE_PATH] + command_args + sys.argv[1:]

    # print(f"Executing command: {' '.join(command)}")
    try:
        process = subprocess.Popen(command, env=os.environ)
        process.wait() # Wait for the process to complete
        if process.returncode != 0:
            # print(f"dbmate command exited with code {process.returncode}", file=sys.stderr)
            pass # dbmate itself usually prints errors.
        sys.exit(process.returncode)
    except FileNotFoundError:
        print(f"Error: dbmate executable not found at {DBMATE_PATH}.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error executing dbmate: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
