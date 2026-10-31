"""One-command local demo: Python + checked-in web build + SQLite.

Python 3.12 is the only runtime prerequisite. The first run installs pinned
Python packages into this repository's private virtual environment.
"""

import argparse
import hashlib
import os
import secrets
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import venv
import webbrowser
from pathlib import Path


ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
BUILD = ROOT / "demo-web"
DATA = ROOT / ".local-data"
VENV = ROOT / ".venv"
PYTHON = VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
REQUIREMENTS = BACKEND / "requirements.txt"
STAMP = VENV / ".ostrov-requirements.sha256"


def prepare() -> dict[str, str]:
    if sys.version_info < (3, 12):
        raise RuntimeError("Нужен Python 3.12 или новее.")
    required = ("index.html", "favicon.ico", "favicon.svg")
    if not all((BUILD / name).is_file() for name in required) or not (BUILD / "assets").is_dir():
        raise RuntimeError("Нет папки demo-web. Скачайте полный архив репозитория.")

    DATA.mkdir(exist_ok=True)
    if not PYTHON.is_file():
        print("Создаю локальное окружение Python…", flush=True)
        venv.EnvBuilder(with_pip=True).create(VENV)

    digest = hashlib.sha256(REQUIREMENTS.read_bytes()).hexdigest()
    if not STAMP.is_file() or STAMP.read_text(encoding="ascii") != digest:
        print("Устанавливаю зависимости. На первом запуске нужен интернет…", flush=True)
        subprocess.run([str(PYTHON), "-m", "pip", "install", "--disable-pip-version-check",
                        "-r", str(REQUIREMENTS)], check=True, cwd=ROOT)
        STAMP.write_text(digest, encoding="ascii")

    secret_file = DATA / "jwt-secret.txt"
    if not secret_file.is_file():
        secret_file.write_text(secrets.token_urlsafe(48), encoding="ascii")
    env = os.environ.copy()
    env.update({
        "DATABASE_URL": "sqlite:///../.local-data/island.sqlite3",
        "JWT_SECRET": secret_file.read_text(encoding="ascii"),
        "DEMO_MODE": "true",
        "FRONTEND_DIST": str(BUILD),
    })
    print("Подготавливаю локальную базу…", flush=True)
    subprocess.run([str(PYTHON), "-m", "alembic", "upgrade", "head"],
                   check=True, cwd=BACKEND, env=env)
    return env


def main() -> int:
    parser = argparse.ArgumentParser(description="Запустить Остров Денег без Docker")
    parser.add_argument("--port", type=int, default=8080, help="порт браузера (по умолчанию 8080)")
    parser.add_argument("--lan", action="store_true", help="открыть доступ устройствам в одной сети")
    parser.add_argument("--no-browser", action="store_true", help="не открывать браузер автоматически")
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("порт должен быть от 1 до 65535")

    try:
        host = "0.0.0.0" if args.lan else "127.0.0.1"
        with socket.socket() as probe:
            probe.bind((host, args.port))
        env = prepare()
        process = subprocess.Popen([str(PYTHON), "-m", "uvicorn", "app.main:app",
                                    "--host", host, "--port", str(args.port)],
                                   cwd=BACKEND, env=env)
        try:
            url = f"http://127.0.0.1:{args.port}/"
            for _ in range(60):
                if process.poll() is not None:
                    raise RuntimeError("Сервер завершился при запуске. Проверьте сообщение выше.")
                try:
                    with urllib.request.urlopen(url + "api/health", timeout=1) as response:
                        if response.status == 200:
                            break
                except (urllib.error.URLError, TimeoutError):
                    time.sleep(0.2)
            else:
                raise RuntimeError("Сервер не ответил в течение 12 секунд.")
            print(f"\nОстров Денег открыт: {url}", flush=True)
            if args.lan:
                print(f"На телефоне в той же сети: http://<IPv4-адрес компьютера>:{args.port}/", flush=True)
            print("Для остановки нажмите Ctrl+C. Данные сохраняются в .local-data.\n", flush=True)
            if not args.no_browser:
                webbrowser.open(url)
            process.wait()
            return process.returncode or 0
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
    except OSError as exc:
        print(f"Не удалось открыть порт {args.port}: {exc}", file=sys.stderr)
        return 1
    except (RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"Запуск остановлен: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
