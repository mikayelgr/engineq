import os
import subprocess
import sys
from dotenv import load_dotenv

def modify_postgres_url(url: str) -> str:
    if not url:
        return ""
    if url.startswith("postgres+asyncpg://"):
        return url.replace("postgres+asyncpg://", "postgresql://", 1)
    elif url.startswith("postgresql+asyncpg://"): # Also handle this variation
        return url.replace("postgresql+asyncpg://", "postgresql://", 1)
    return url

def run_sqlacodegen():
    # Construct .env path relative to this script's location (acura/scripts/.env)
    # then go up one level to acura/.env
    dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    load_dotenv(dotenv_path=dotenv_path)

    postgres_url = os.getenv("POSTGRES_URL")
    if not postgres_url:
        print("Error: POSTGRES_URL is not set in .env or environment.", file=sys.stderr)
        sys.exit(1)

    modified_url = modify_postgres_url(postgres_url)

    output_file_path = os.path.join(
        os.path.dirname(__file__), "..", "internal", "models", "codegen", "models.py"
    )
    output_dir = os.path.dirname(output_file_path)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory: {output_dir}")

    try:
        # Execute sqlacodegen
        # Ensure environment variables are passed to subprocess if sqlacodegen relies on them
        # (though it primarily uses the URL)
        env = os.environ.copy()
        process = subprocess.run(
            ["sqlacodegen", modified_url],
            capture_output=True,
            text=True,
            check=False, # Check manually to provide better error messages
            env=env
        )

        if process.returncode != 0:
            print(f"Error running sqlacodegen. Return code: {process.returncode}", file=sys.stderr)
            print(f"Stdout: {process.stdout}", file=sys.stderr)
            print(f"Stderr: {process.stderr}", file=sys.stderr)
            # Attempt to read POSTGRES_DB from env for more context if available
            db_name = os.getenv("POSTGRES_DB", "N/A")
            print(f"Attempted to connect to database: {db_name} using URL: {modified_url}", file=sys.stderr)
            sys.exit(1)

        generated_code = process.stdout

        lines = generated_code.splitlines()
        actual_code = generated_code

        # More robust header skipping for sqlacodegen output
        # It often starts with "# coding: utf-8" and might have a "Using pgvector..." line
        if lines:
            if lines[0].strip() == "# coding: utf-8":
                if len(lines) > 1 and "Using pgvector" in lines[1]:
                    actual_code = "\n".join([lines[0]] + lines[2:])
                else:
                    # Only #coding: utf-8, no pgvector line after it
                    actual_code = "\n".join(lines)
            elif "Using pgvector" in lines[0]:
                actual_code = "\n".join(lines[1:])

        with open(output_file_path, "w") as f:
            f.write(actual_code)

        print(f"Successfully generated models to {output_file_path}")

    except FileNotFoundError:
        print("Error: sqlacodegen command not found. Is it installed (e.g., via pyproject.toml with uv) and in PATH within the uv environment?", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    run_sqlacodegen()
