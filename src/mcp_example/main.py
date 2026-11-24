"""Deprecated shim. The server now lives in the qauto_mcp package: run `python -m qauto_mcp`."""

from qauto_mcp.__main__ import main

if __name__ == "__main__":
    main()
