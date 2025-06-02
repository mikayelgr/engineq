# Project EngineQ Monorepo

This repository contains the services and tools for Project EngineQ.

## Overview

This monorepo hosts Project EngineQ, a sophisticated music curation and playback system. It comprises several key components that work together:

*   **`acura/` (Acura Curation Engine):**
    This is an asynchronous Python backend service responsible for the intelligent curation of music playlists. It operates as a worker, listening for messages on a RabbitMQ queue ("acura").
    *   **Core Functionality:** When triggered by a message (containing a subscriber's license key), Acura fetches the subscriber's textual prompt (describing desired music ambiance) from PostgreSQL. It then employs a multi-step pipeline (`MusicDiscoveryPipeline` using `pydantic-graph`):
        1.  **AI-Powered Query Generation:** Uses an LLM (configurable: OpenAI `gpt-4o-mini` or a local Ollama model via `internal/agents/decide_llm()`) to transform the user prompt into effective search queries for Spotify.
        2.  **Dynamic Curation Strategy:** Generates embeddings (via OpenAI `text-embedding-3-large`) for the search query and leverages PostgreSQL with `pgvector` for similarity searches against existing curated tracks. It intelligently decides whether to find entirely new content or reuse/supplement existing similar content.
        3.  **New Content Discovery:** If new content is needed, it searches the Spotify API for relevant playlists. An LLM then validates if these playlists match the user's intent. For suitable tracks (non-explicit), it finds corresponding YouTube music videos via the Brave Search API, verifies their relevance (using Levenshtein distance), generates contextualized track embeddings, and stores the track metadata (title, YouTube URL, artist, duration, Spotify image) and embeddings in PostgreSQL.
        4.  **Existing Content Reuse:** If reusing content, it identifies similar tracks from the database (excluding those recently suggested) and adds them to the playlist.
    *   **Interface:** Primarily interacts via RabbitMQ messages. It does not expose HTTP APIs directly.
    *   **Key Technologies:** Python, `asyncio`, `aio_pika` (RabbitMQ), `asyncpg` (PostgreSQL), `pgvector`, `SQLAlchemy`, `pydantic-graph`, `pydantic-ai`, OpenAI API (LLMs and embeddings), Spotify API, Brave Search API.

*   **`ui/` (User Interface & User Backend):**
    This is a Next.js application that serves as the primary user interface and also handles direct user-facing backend logic.
    *   **Core Functionality:**
        1.  **User Onboarding & Authentication:** Provides a license-key based authentication system. Users sign in with their key, which is validated against the PostgreSQL database and stored in an HTTP-only cookie. Middleware protects dashboard and API routes.
        2.  **Music Playback Dashboard:** The main interface after login, featuring a music player, a dynamic playback queue, and display of current track information.
        3.  **Prompt Management:** Allows users to view and manage their music preference prompts (which `acura` uses for curation) via Server Actions that directly update the PostgreSQL database.
        4.  **Proactive Curation Trigger:** The UI monitors the user's playback queue. If the number of remaining tracks falls below a threshold (e.g., 10), the UI's backend (a Next.js API route at `/api/tracklist`) automatically sends a message to the `acura` RabbitMQ queue, requesting new content curation for that user.
        5.  **Playback Progress Tracking:** Updates the backend (`/api/update-last-played` Next.js API route) with the last track played by the user, allowing the system to serve only unplayed portions of playlists.
    *   **Architecture:** Acts as a "Backend For Frontend (BFF)". Its server-side capabilities (Next.js API Routes and Server Actions) interact directly with PostgreSQL for user-specific data and with RabbitMQ to trigger `acura`'s asynchronous processing.
    *   **Key Technologies:** Next.js (App Router), React, Tailwind CSS, HeroUI, Zustand (client-state), `@tanstack/react-query` (server-state), `postgres` (pg library for direct DB access), `amqplib` (RabbitMQ).

*   **`migrations/`**: Contains SQL database migration scripts. These are managed by `dbmate` and define the schema for the PostgreSQL database used by both `acura` and `ui`.

*   **`migrator/`**: This directory previously held `npm` configuration for `dbmate`. Now, it primarily contains `.env.example` for `dbmate`'s `DATABASE_URL`. The `dbmate` tool itself is executed via a Python script (`acura/scripts/run_dbmate_cli.py`) managed under the `acura` project's `uv` environment. This script automatically downloads the appropriate `dbmate` binary.

## Prerequisites for Development

*   **Python**: Version 3.11+ (as specified in `acura/pyproject.toml`).
*   **`uv`**: The Python package manager used for the `acura` backend and migration tooling. Install from [https://github.com/astral-sh/uv](https://github.com/astral-sh/uv).
*   **Node.js**: For the `ui/` frontend (check `ui/package.json` for specific version, e.g., >=18.x).
*   **`npm` or `yarn`**: For managing frontend dependencies.
*   **Docker & Docker Compose**: Recommended for running dependent services like PostgreSQL and RabbitMQ, and for containerized deployment.
*   **`make`**: A `Makefile` may be provided for common commands (optional, but good practice).

## Local Development Setup

### 1. Clone the Repository

```bash
git clone <repository_url>
cd <repository_name>
```

### 2. Dependent Services

It's highly recommended to use Docker Compose to manage backing services. You can find all docker-related files inside the `docker` folder in the project's root.

Start these services:
```bash
docker-compose up -d
```

### 3. Backend (`acura/`)

*   **Set up Environment Variables:**
    Copy `acura/.env.example` to `acura/.env` and fill in the necessary values, especially:
    *   `POSTGRES_URL`: Should point to your PostgreSQL container (e.g., `postgresql+asyncpg://postgres:postgres@localhost:5432/engineq`)
    *   `AMQP_URL`: Should point to your RabbitMQ container (e.g., `amqp://guest:guest@localhost:5672/`)
    *   `OPENAI_API_KEY`, etc.

*   **Install Dependencies using `uv`:**
    ```bash
    cd acura
    uv pip sync pyproject.toml
    cd ..
    ```

*   **Run Database Migrations:**
    The `migrator/` tool is now managed via a Python script.
    First, copy `migrator/.env.example` to `migrator/.env` and set `DATABASE_URL`:
    *   `DATABASE_URL="postgresql://postgres:postgres@localhost:5432/engineq?sslmode=disable"`

    Then run migrations using `uv` from the project root:
    ```bash
    uv run dbmate-cli up
    ```
    (This invokes the `acura.scripts.run_dbmate_cli:main` script defined in `acura/pyproject.toml`)
    Common `dbmate` commands (`new <name>`, `down`, `status`) can be passed after `uv run dbmate-cli`.

*   **Generate Database Models (if schema changed):**
    ```bash
    uv run generate-db-models
    ```
    (This invokes `acura.scripts.generate_models:run_sqlacodegen`)

*   **Run the Acura Application:**
    (Instructions depend on how `acura/__main__.py` is structured. Assuming it starts a server or worker)
    ```bash
    cd acura
    uv run python __main__.py
    # Or if it's a web app, e.g., uv run uvicorn acura.main:app --reload
    cd ..
    ```

### 4. Frontend (`ui/`)

*   **Set up Environment Variables:**
    Copy `ui/.env.example` to `ui/.env.local` (Next.js convention) and fill in any required values.

*   **Install Dependencies:**
    ```bash
    cd ui
    npm install # or yarn install
    ```

*   **Run the Development Server:**
    ```bash
    npm run dev # or yarn dev
    cd ..
    ```
    The UI should now be accessible, typically at `http://localhost:3000`.

## Deployment

This section provides general guidance. Specific deployment strategies may vary based on your infrastructure.

### `acura` (Backend Service)

*   **Containerization:** A `Dockerfile` is provided in `acura/`. Build the Docker image:
    ```bash
    docker build -t engineq-acura ./acura
    ```
*   **Environment Variables:** Ensure all required environment variables from `acura/.env.example` are set in the deployment environment (e.g., `POSTGRES_URL`, `AMQP_URL`, `OPENAI_API_KEY`, `LOGFIRE_TOKEN`, secrets for external services). `DEBUG` should be set to `0` or `False` in production.
*   **Required Services:** Needs access to a running PostgreSQL database and RabbitMQ instance.
*   **Execution:** Run the Docker container, ensuring it's connected to the necessary network and services.
    ```bash
    docker run -d --name engineq_acura_app \
          --network your_network_name \
          -e POSTGRES_URL="<production_postgres_url>" \
          -e AMQP_URL="<production_amqp_url>" \
          # ... other env vars ... \
          engineq-acura
    ```

### `ui` (Frontend Service)

*   **Containerization:** A `Dockerfile` is provided in `ui/`. This typically builds the Next.js app and serves it using a Node.js server.
    ```bash
    docker build -t engineq-ui ./ui
    ```
*   **Environment Variables:** Set any `NEXT_PUBLIC_` variables required at runtime or build time, as configured in your Next.js app and `ui/.env.example`.
*   **Execution:** Run the Docker container.
    ```bash
    docker run -d --name engineq_ui_app -p 3000:3000 engineq-ui
    ```
    Alternatively, if your Next.js app is built as static HTML (`next export`), you can serve these static files using a web server like Nginx.

### Database Migrations (`migrator`)

*   Migrations should be run as part of your deployment process *before* deploying new versions of the `acura` application that might depend on schema changes.
*   The `uv run dbmate-cli up` command (executed within an environment that has Python, `uv`, and access to the target database) is used to apply migrations.
*   Ensure `DATABASE_URL` is set correctly for the target environment where migrations are being applied.
*   The `migrator/bin/dbmate` binary will be downloaded automatically by the script if not present. Ensure the execution environment has internet access for the first run or if the binary is cleared.

## Environment Variables Summary

Refer to the `.env.example` files in each subproject for a comprehensive list. Key variables include:

*   **`acura/.env.example`**:
    *   `DEBUG`: Set to `0` for production.
    *   `POSTGRES_URL`: Connection string for PostgreSQL.
    *   `AMQP_URL`: Connection string for RabbitMQ.
    *   `OPENAI_API_KEY`, `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`, `LOGFIRE_TOKEN`, etc.: API keys and secrets for external services.
*   **`ui/.env.example`**:
    *   Variables prefixed with `NEXT_PUBLIC_` are exposed to the browser.
    *   Other variables might be used during the build process or server-side rendering.
*   **`migrator/.env.example`**:
    *   `DATABASE_URL` (or `LOCAL`, `PRODUCTION`, `STAGING`): Used by `dbmate` to connect to the database for migrations.

Always ensure that sensitive information like API keys and database credentials are managed securely and not hardcoded into the application or committed to version control (use environment variables or a secrets management system).
