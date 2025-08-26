import argparse
import logging
import socket

import uvicorn


def is_local_environment():
    """Check if running in local development environment."""
    hostname = socket.gethostname()
    return hostname in ["localhost", "127.0.0.1"] or hostname.endswith(".local")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the FastAPI server with Uvicorn")
    parser.add_argument(
        "--host", type=str, default="0.0.0.0", help="Host to run the server on"
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="Port to run the server on"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        default=is_local_environment(),
        help="Enable auto-reload for development",
    )
    parser.add_argument(
        "--workers", type=int, default=1, help="Number of worker processes"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="info",
        choices=["debug", "info", "warning", "error", "critical"],
        help="Logging level",
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run the server
    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers,
        log_level=args.log_level,
    )
