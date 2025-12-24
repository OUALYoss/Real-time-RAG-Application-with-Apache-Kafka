import argparse
import subprocess
import sys
import os
import multiprocessing


def run_ingestion():
    """Run the ingestion main function."""
    from src.ingestion.main import main as ingestion_main

    ingestion_main()


def run_processing():
    """Run the processing main function."""
    from src.processing.main import main as processing_main

    processing_main()


def run_api():
    """Run the API main function."""
    from src.api.main import main as api_main

    api_main()


def run_dashboard():
    """Run the dashboard Streamlit app."""
    dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard", "app.py")
    subprocess.run([sys.executable, "-m", "streamlit", "run", dashboard_path])


def run_embed():
    """Run the embedding builder main function."""
    from src.rag.builder import main as embed_main

    embed_main()


def main():
    parser = argparse.ArgumentParser(
        description="Real-time RAG Application Orchestrator"
    )
    parser.add_argument(
        "command",
        choices=["ingest", "process", "embed", "api", "dashboard", "all"],
        help="Command to run: ingest, process, embed, api, dashboard, or all",
    )

    args = parser.parse_args()

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
        print("Running all components in parallel...")
        processes = []

        # Start ingestion
        p_ingest = multiprocessing.Process(target=run_ingestion)
        p_ingest.start()
        processes.append(p_ingest)
        print("Ingestion started")

        # Start processing
        p_process = multiprocessing.Process(target=run_processing)
        p_process.start()
        processes.append(p_process)
        print("Processing started")

        # Start embedding
        p_embed = multiprocessing.Process(target=run_embed)
        p_embed.start()
        processes.append(p_embed)
        print("Embedding started")

        # Start API
        p_api = multiprocessing.Process(target=run_api)
        p_api.start()
        processes.append(p_api)
        print("API started")

        # Start dashboard
        p_dashboard = multiprocessing.Process(target=run_dashboard)
        p_dashboard.start()
        processes.append(p_dashboard)
        print("Dashboard started")

        # Wait for all processes (though they run indefinitely)
        for p in processes:
            p.join()



if __name__ == "__main__":
    main()
