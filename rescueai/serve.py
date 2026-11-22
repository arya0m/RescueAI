"""
Unified Server Command for RescueAI Operations Console
Serves FastAPI and static frontend assets on a single unified port.
"""

import argparse
import sys
import uvicorn


def run_server():
    parser = argparse.ArgumentParser(description="RescueAI Operations Console Server")
    parser.add_argument("command", nargs="?", default="serve", help="Command to run (default: serve)")
    parser.add_argument("--host", default="0.0.0.0", help="Host address to bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind (default: 8000)")
    parser.add_argument("--reload", action="store_true", help="Enable hot reload for development")
    
    args, unknown = parser.parse_known_args()
    
    if args.command == "serve":
        print(f"[RescueAI] Starting Operations Server on http://{args.host}:{args.port}")
        uvicorn.run(
            "rescueai.api.app:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level="info"
        )
    else:
        print(f"Unknown command '{args.command}'. Usage: python -m rescueai serve [--port 8000]")
        sys.exit(1)


if __name__ == "__main__":
    run_server()
