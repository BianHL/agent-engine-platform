"""CLI entry point for the MCP server.

Usage:
    python -m app.mcp                # stdio transport (default)
    python -m app.mcp --transport stdio
"""
import argparse
import asyncio
import logging
import sys

from app.mcp.server import MCPServer


def main() -> None:
    parser = argparse.ArgumentParser(description="Agent Engine Platform MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio"],
        default="stdio",
        help="Transport type (default: stdio)",
    )
    parser.add_argument(
        "--log-level",
        default="WARNING",
        help="Log level (default: WARNING)",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.WARNING),
        stream=sys.stderr,
    )

    server = MCPServer()

    if args.transport == "stdio":
        asyncio.run(server.run_stdio())
    else:
        print(f"Unsupported transport: {args.transport}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
