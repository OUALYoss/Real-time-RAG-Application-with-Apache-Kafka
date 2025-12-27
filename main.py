import argparse
import subprocess
import sys
import os
import multiprocessing
import logging


def setup_logging(component: str):
    logging.basicConfig(
        level=logging.INFO,
        format=f"[%(processName)s | PID %(process)d | {component}] %(levelname)s - %(message)s",
    )


def setup_logging(name):
    """Configure logging for a specific component."""
    logging.basicConfig(
        level=logging.INFO,
        format=f"%(asctime)s [%(levelname)s] {name}: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )


def setup_logging(name):
    """Configure logging for a specific component."""
    logging.basicConfig(
        level=logging.INFO,
        format=f"%(asctime)s [%(levelname)s] {name}: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )


def run_ingestion():
    setup_logging("INGESTION")
    logging.info("Starting ingestion service")
    from src.ingestion.main import main as ingestion_main

    ingestion_main()


def run_processing():
    setup_logging("PROCESSING")
    logging.info("Starting processing service")
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
    setup_logging("API")
    logging.info("Starting API service")
    from src.api.main import main as api_main

    api_main()


def run_dashboard():
    setup_logging("DASHBOARD")
    logging.info("Starting dashboard service")
    dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard", "app.py")
    subprocess.run([sys.executable, "-m", "streamlit", "run", dashboard_path])


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
        logging.info("Running all components in parallel...")

        processes = []

        def start_process(name, target):
            p = multiprocessing.Process(target=target, name=name)
            p.start()
            logging.info(f"{name} started (PID {p.pid})")
            processes.append(p)

        start_process("INGESTION", run_ingestion)
        start_process("PROCESSING", run_processing)
        start_process("EMBEDDING", run_embed)
        start_process("API", run_api)
        start_process("DASHBOARD", run_dashboard)

        for p in processes:
            p.join()


if __name__ == "__main__":
    main()