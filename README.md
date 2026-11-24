# mcp-example

An MCP server for the QAuto garage REST API. The default transport is Streamable HTTP.

- Tools: `signup`, `signin`, `add_car`, `get_cars`, `get_brands`, `get_models`.
- Resources: `qauto://cars/catalog`, `qauto://cars/brands/{brand_id}`.
- Prompts: `analyze_cars`.

## Install

Requires `uv`.

```bash
uv sync
cp .env.example .env
```

Fill in the values in `.env`. See [Settings](#settings).

## Run the server

```bash
uv run python -m qauto_mcp
```

The server listens on `http://127.0.0.1:8000/mcp`. Logs go to stderr. `GET /health` returns the server status. To stop the server, press `Ctrl+C`.

More logs for one run:

```bash
LOG_LEVEL=DEBUG uv run python -m qauto_mcp       # tool calls + HTTP bodies (secrets masked)
MCP_LOG_LEVEL=DEBUG uv run python -m qauto_mcp   # framework and transport details
```

Note: The old stdio mode is still available: `MCP_TRANSPORT=stdio uv run python -m qauto_mcp`.

## Run in Docker

The image has Python, uv, the dependencies and the code. You need only Docker with Compose.

1. Stop the local server (`uv run python -m qauto_mcp`). Both use port 8000.
2. Build and start the container:

   ```bash
   docker compose up -d --build
   ```

3. Check the container:

   ```bash
   curl -s http://127.0.0.1:8000/health
   ```

   The server returns `{"status":"ok","mcp":"/mcp"}`.
4. Reload the MCP server in the Host. The URL does not change: `http://127.0.0.1:8000/mcp`.

Other commands:

```bash
docker compose ps                              # status and health
docker compose logs -f                         # server logs
docker compose restart                         # restart without rebuild
docker compose up -d --build                   # rebuild after a code change
DOCKER_LOG_LEVEL=DEBUG docker compose up -d    # start with LOG_LEVEL=DEBUG
docker compose down                            # stop and remove the container
```

To go back to the local server, run `docker compose down`, then `uv run python -m qauto_mcp`.

If port 8000 is busy, find the process:

```bash
lsof -nP -iTCP:8000 -sTCP:LISTEN
```

- `Python`: the local server. Stop it with `Ctrl+C` in its terminal.
- `com.docke...`: the container. Stop it with `docker compose down`.

Notes:

- If the shell does not find `docker`, start Docker Desktop and add its CLI to `PATH`: `export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"`.

- `compose.yaml` sets `MCP_HOST=0.0.0.0`. Inside a container, `127.0.0.1` is the container itself, so the published port would not work.
- `environment` in `compose.yaml` overrides the same variables from `.env`. `LOG_LEVEL` in the container is `INFO`, unless you set `DOCKER_LOG_LEVEL`.
- `.env` is not in the image (`.dockerignore`). Compose passes it to the container at start as the credentials fallback. If all clients send headers, remove `QAUTO_EMAIL` and `QAUTO_PASSWORD` from `.env`.
- The port is published only on `127.0.0.1`. The server has no auth. For access from the LAN, change it to `"8000:8000"` and use the host IP.
- The container runs as the non-root user `app` (uid 1000) and restarts automatically (`restart: unless-stopped`).

## Connect a Host

The Host does not start the server process. Start the server first, then connect the Host by URL.

The client sends the QAuto credentials in HTTP headers:

```json
{
  "mcpServers": {
    "mcp-example": {
      "type": "http",
      "url": "http://127.0.0.1:8000/mcp",
      "headers": {
        "QAUTO_EMAIL": "your_user@example.com",
        "QAUTO_PASSWORD": "YourPass1"
      }
    }
  }
}
```

- The server also accepts `X-QAuto-Email` and `X-QAuto-Password`.
- If the headers are empty, the server uses `QAUTO_EMAIL` and `QAUTO_PASSWORD` from its `.env`.
- `.mcp.json` (Claude Code) takes the header values from the shell variables `QAUTO_EMAIL` and `QAUTO_PASSWORD`. If they are not set, the server uses `.env`.
- `.cursor/mcp.json` has only `url`. Add `headers` to it if you need other credentials.

`add_car` and `get_cars` sign in automatically. If the email in the headers changes, the server signs in again.

To reconnect after a change in the config or after a server restart:

- Claude Code: run `/mcp` and select `mcp-example`.
- Cursor: **Settings → MCP**, then reload `mcp-example`.

## Settings

Copy `.env.example` to `.env` and fill in the values.

| Variable | Set in | Purpose |
|---|---|---|
| `QAUTO_EMAIL`, `QAUTO_PASSWORD` | Client headers (fallback: server `.env`) | Automatic signin for tools |
| `QAUTO_BASE_URL`, `QAUTO_TIMEOUT` | Server `.env` | QAuto API for the httpx client |
| `MCP_TRANSPORT` | Server `.env` or shell | `streamable-http` (default) or `stdio` |
| `MCP_HOST`, `MCP_PORT`, `MCP_HTTP_PATH` | Server `.env` | Where the MCP endpoint listens |
| `MCP_LOG_LEVEL` | Server `.env` | Framework and transport logs |
| `LOG_LEVEL` | Server `.env` | Application logs: tool calls, HTTP calls to QAuto |
| `LOG_HTTP_BODIES` | Server `.env` | Log request and response bodies (only with `LOG_LEVEL=DEBUG`) |
| `LOG_BODY_MAX_CHARS` | Server `.env` | Maximum length of a logged body |

The server masks secrets in logs (`password`, `repeatPassword`, `sid`, `cookie`, `authorization`) as `***`.

## Structure

```
src/qauto_mcp/
├── __main__.py        # python -m qauto_mcp, transport selection
├── server.py          # MCPServer + instructions + lifespan + tool-call logging + /health
├── config.py          # settings from env
├── logging_setup.py   # application logging, secret masking
├── formatting.py      # one error format for all tools
├── models/            # Pydantic input models (no network, no MCP)
├── services/          # http_client (with logging hooks), session, catalog
├── tools/             # signup, signin, add_car, get_cars, get_brands, get_models
├── resources/         # qauto://cars/catalog, qauto://cars/brands/{brand_id}
└── prompts/           # analyze_cars
```

Dependencies go only down: `tools/resources/prompts → models + services + formatting → config`.

`src/mcp_example/main.py` is a deprecated shim for old Host configs.

## Run with MCP Inspector

Requires Node.js (`npx`) and `uv`.

1. Start the server: `uv run python -m qauto_mcp` or `docker compose up -d`.
2. In a second terminal, run `npx @modelcontextprotocol/inspector`.
3. Open the URL with the token from the terminal.
4. Set **Transport Type** to **Streamable HTTP** and **URL** to `http://127.0.0.1:8000/mcp`.
5. Optional: add the `QAUTO_EMAIL` and `QAUTO_PASSWORD` headers in the authentication or headers panel.
6. Click **Connect**. Then open **Tools** and run `get_cars`.

Note: For the stdio mode, the Inspector starts the server itself:
`npx @modelcontextprotocol/inspector -e MCP_TRANSPORT=stdio uv run --directory /Users/ievgen/Documents/mcp-example python -m qauto_mcp`.

## Interview preparation

[docs/interview-questions.md](docs/interview-questions.md): MCP questions with short answers, grouped by course topic, plus practical tasks on this project.

## Debug with PyCharm

1. Create a run configuration: **Module name** `qauto_mcp`, working directory is the project root.
2. Set a breakpoint in a file in `src/qauto_mcp/tools/`.
3. Start the configuration in **Debug** mode.
4. Connect the Inspector or the Host and call the tool.

Note: If you stop on a breakpoint for more than 10 seconds, increase **Request Timeout** in the Inspector **Configuration** panel.
