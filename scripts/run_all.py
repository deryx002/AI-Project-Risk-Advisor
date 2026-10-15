import os
import sys
import time
import subprocess
import signal
import threading
from pathlib import Path

# Paths
ROOT_DIR = Path(__file__).resolve().parent.parent
DOC_DIR = ROOT_DIR / "services" / "document-service"
RAG_DIR = ROOT_DIR / "services" / "rag-service"
FRONTEND_DIR = ROOT_DIR / "frontend"

# Automatically detect virtual environment Python if present
VENV_WINDOWS = ROOT_DIR / ".venv" / "Scripts" / "python.exe"
VENV_UNIX = ROOT_DIR / ".venv" / "bin" / "python"

if VENV_WINDOWS.exists():
    PYTHON_EXE = str(VENV_WINDOWS)
elif VENV_UNIX.exists():
    PYTHON_EXE = str(VENV_UNIX)
else:
    PYTHON_EXE = sys.executable

processes = []


def kill_existing_on_ports(ports=(8000, 8002, 8501)):
    """Clean up any leftover processes on the required ports before starting."""
    if sys.platform != "win32":
        return
    for port in ports:
        try:
            cmd = f'powershell -Command "Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess"'
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
            pids = set(result.stdout.strip().split())
            current_pid = str(os.getpid())
            for pid in pids:
                if pid and pid != current_pid and pid != "0":
                    subprocess.run(f"taskkill /F /PID {pid}", capture_output=True, shell=True)
        except Exception:
            pass


def signal_handler(sig, frame):
    print("\n[Shutdown] Stopping all services...")
    for item in processes:
        p = item[1] if isinstance(item, tuple) else item
        try:
            p.terminate()
            p.wait(timeout=2)
        except Exception:
            try:
                p.kill()
            except Exception:
                pass
    print("[Shutdown] All services stopped.")
    sys.exit(0)


def stream_logs(pipe, prefix):
    """Continuously reads stdout/stderr so child processes never buffer-deadlock."""
    try:
        for line in iter(pipe.readline, ""):
            line_str = line.strip()
            if line_str:
                print(f"{prefix} {line_str}")
    except Exception:
        pass
    finally:
        pipe.close()


def start_service(name: str, prefix: str, cmd: list, cwd: Path):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(cwd)
    proc = subprocess.Popen(
        cmd,
        cwd=str(cwd),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    processes.append((name, proc))
    t = threading.Thread(target=stream_logs, args=(proc.stdout, prefix), daemon=True)
    t.start()
    return proc


def main():
    signal.signal(signal.SIGINT, signal_handler)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, signal_handler)

    print("=" * 70)
    print("  AI Project Risk Advisor - Service Launcher")
    print("=" * 70)
    print(f"[*] Python environment: {PYTHON_EXE}")

    print("[*] Checking and freeing ports 8000, 8002, 8501...")
    kill_existing_on_ports()
    time.sleep(1)

    # 1. Start Document Service (:8000)
    print("[*] Launching Document Service on port 8000...")
    start_service(
        "Document Service",
        "[DocService]",
        [PYTHON_EXE, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000", "--log-level", "warning"],
        DOC_DIR,
    )

    # 2. Start RAG Service (:8002)
    print("[*] Launching RAG Service on port 8002...")
    start_service(
        "RAG Service",
        "[RAGService]",
        [PYTHON_EXE, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8002", "--log-level", "warning"],
        RAG_DIR,
    )

    # Wait 2 seconds for services to bind
    time.sleep(2)

    # 3. Start Streamlit Frontend (:8501)
    print("[*] Launching Streamlit UI on port 8501...")
    start_service(
        "Streamlit UI",
        "[Streamlit]",
        [PYTHON_EXE, "-m", "streamlit", "run", "app.py", "--server.port", "8501", "--server.headless", "true"],
        FRONTEND_DIR,
    )

    print("\n" + "=" * 70)
    print("  All services launched successfully.")
    print("  - Document Service API: http://127.0.0.1:8000/docs")
    print("  - RAG Service API:      http://127.0.0.1:8002/docs")
    print("  - Streamlit Dashboard:  http://localhost:8501")
    print("=" * 70)
    print("Press Ctrl+C to terminate all services.\n")

    reported_exits = set()
    try:
        while True:
            for name, p in processes:
                if p.poll() is not None and p not in reported_exits:
                    reported_exits.add(p)
                    print(f"[Warning] {name} exited with code {p.returncode}")
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(None, None)


if __name__ == "__main__":
    main()
