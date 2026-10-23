"""Verify startup and PostgreSQL persistence in an isolated, disposable Compose project.

Uses separate ports and a unique volume. Never removes the development project's volume.
Requires Docker access and network for uncached builds.
"""
import os
import subprocess
import time
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
project = f"agipreve-acceptance-{uuid4().hex[:10]}"
command = ["docker", "compose", "--project-name", project, "-f", str(ROOT / "compose.yaml")]
environment = {**os.environ, "API_PORT": "18080", "POSTGRES_PORT": "15432"}


def run(*arguments: str, capture=False):
    return subprocess.run(
        [*command, *arguments], cwd=ROOT, env=environment,
        check=True, text=True, capture_output=capture, timeout=240,
    )


if __name__ == "__main__":
    try:
        run("up", "--build", "-d", "--wait", "--wait-timeout", "120")
        run("exec", "-T", "db", "sh", "-c",
            'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" '
            '-c "CREATE TABLE acceptance_probe (id integer PRIMARY KEY); '
            'INSERT INTO acceptance_probe VALUES (1);"')
        run("restart", "db")
        for attempt in range(30):
            result = subprocess.run(
                [*command, "exec", "-T", "db", "sh", "-c",
                 'pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"'],
                cwd=ROOT, env=environment, capture_output=True, timeout=10,
            )
            if result.returncode == 0:
                break
            time.sleep(1)
        output = run("exec", "-T", "db", "sh", "-c",
            'psql -v ON_ERROR_STOP=1 -At -U "$POSTGRES_USER" -d "$POSTGRES_DB" '
            '-c "SELECT count(*) FROM acceptance_probe WHERE id=1"', capture=True)
        if output.stdout.strip() != "1":
            raise RuntimeError("Persistence check failed")
        run("exec", "-T", "api", "python", "-c",
            "import urllib.request; "
            "assert urllib.request.urlopen('http://localhost:8000/health', timeout=10).status == 200")
        print("PASS: clean startup, migrations, seed, health and persistence after database restart.")
    finally:
        # Only this randomly named acceptance project's containers/network/volume are removed.
        subprocess.run([*command, "down", "--volumes"], cwd=ROOT, env=environment, timeout=60)
