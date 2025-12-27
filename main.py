import argparse
import subprocess
import sys
import os
import multiprocessing
import time
import signal
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("orchestrator")


def run_ingestion():
    """Run the ingestion main function."""
    try:
        from src.ingestion.main import main as ingestion_main

        ingestion_main()
    except Exception as e:
        logger.error(f"Ingestion crashed: {e}")


def run_processing():
    """Run the processing main function."""
    try:
        from src.processing.main import main as processing_main

        processing_main()
    except Exception as e:
        logger.error(f"Processing crashed: {e}")


def run_embed():
    setup_logging("EMBEDDING")
    logging.info("Starting embedding service")
    from src.rag.builder import main as embed_main

    embed_main()


def run_api():
    """Run the API main function via uvicorn subprocess."""
    try:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "src.api.main:app",
                "--host",
                "0.0.0.0",
                "--port",
                "8080",
            ]
        )
    except Exception as e:
        logger.error(f"API crashed: {e}")


def run_dashboard():
    """Run the dashboard Streamlit app."""
    try:
        dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard", "app.py")
        subprocess.run([sys.executable, "-m", "streamlit", "run", dashboard_path])
    except Exception as e:
        logger.error(f"Dashboard crashed: {e}")


def run_embed():
    """Run the embedding builder main function."""
    try:
        from src.rag.builder import main as embed_main

        embed_main()
    except Exception as e:
        logger.error(f"Embedding crashed: {e}")


class Orchestrator:
    def __init__(self):
        self.processes = {}
        self.running = True
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)

    def stop(self, signum, frame):
        logger.info("Shutdown signal received. Stopping all processes...")
        self.running = False
        for name, p in self.processes.items():
            if p.is_alive():
                logger.info(f"Terminating {name}...")
                p.terminate()
        sys.exit(0)

    def start_process(self, name, target):
        p = multiprocessing.Process(target=target, name=name)
        p.start()
        self.processes[name] = p
        logger.info(f"Started {name} (PID: {p.pid})")
        return p

    def run_all(self):
        logger.info("Starting all Disaster RAG components...")
        self.start_process("ingestion", run_ingestion)
        self.start_process("processing", run_processing)
        self.start_process("embedding", run_embed)
        self.start_process("api", run_api)
        self.start_process("dashboard", run_dashboard)

        while self.running:
            time.sleep(5)
            for name, p in list(self.processes.items()):
                if not p.is_alive():
                    if name == "dashboard":
                        logger.info(
                            "Dashboard closed by user. Shutting down orchestrator..."
                        )
                        self.stop(None, None)
                    else:
                        logger.warning(f"Process {name} died! Restarting...")
                        self.start_process(name, p._target)


def main():
    setup_logging("ORCHESTRATOR")

    parser = argparse.ArgumentParser(
        description="Real-time RAG Application Orchestrator"
    )
    parser.add_argument(
        "command",
        choices=["ingest", "process", "embed", "api", "dashboard", "all"],
        help="Command to run",
    )

    args = parser.parse_args()

    logging.info(f"Command received: {args.command}")

    if args.command == "ingest":
        run_ingestion()

    elif args.command == "process":
        run_processing()

    elif args.command == "embed":
        run_embed()

    elif args.command == "api":
        run_api()

    elif args.command == "dashboard":
        run_dashboard()

    elif args.command == "all":
        orchestrator = Orchestrator()
        orchestrator.run_all()


if __name__ == "__main__":
    main()