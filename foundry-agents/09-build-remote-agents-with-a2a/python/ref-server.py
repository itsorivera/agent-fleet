from __future__ import annotations

import os

from dotenv import load_dotenv
import uvicorn

from ref_app import create_app, AgentSpec
from outline_agent.build_agent import build_agent as build_outline_agent
from title_agent.build_agent import build_agent as build_title_agent

def main() -> None:
    load_dotenv(override=True)

    host = os.getenv("SERVER_URL", "localhost")
    port = int(os.getenv("SERVER_PORT", "8000"))

    app = create_app(
        agents=[
            build_outline_agent(base_url=host, port=port),
            build_title_agent(base_url=host, port=port),
        ],
    )
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()