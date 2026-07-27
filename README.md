# Environmental Data Microservices Platform

[![Continuous Integration](https://github.com/aleruizzs/vizzuality-coding-challenge/actions/workflows/ci.yml/badge.svg)](https://github.com/aleruizzs/vizzuality-coding-challenge/actions/workflows/ci.yml)
[![Node.js](https://img.shields.io/badge/Node.js-20.x-339933?logo=node.js)](https://nodejs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178C6?logo=typescript)](https://www.typescriptlang.org/)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)](https://www.docker.com/)

This is my attempt to build a high-performance, containerized microservices platform designed for importing, parsing, aggregating, and querying environmental emissions datasets, as part of the [Vizzuality Code Challenge](https://github.com/Vizzuality/coding-challenge-examples/blob/main/backend-engineer/importer/README.MD).

---

## Architecture & Tech Stack

The platform consists of two decoupled microservices sharing a PostgreSQL database:


| Service | Tech Stack | Responsibilities |
| :--- | :--- | :--- |
| **Importer Service** (`:3000`) | Node.js 20, TypeScript, Express, Drizzle ORM, Multer, `csv-parser` | CSV upload streaming, wide-to-long schema unpivoting, batched DB transactions, post-import aggregation metrics. |
| **Query Service** (`:8000`) | Python 3.11, FastAPI, AsyncSQLAlchemy, AsyncPG, Pydantic | Non-blocking async API, filtering, pagination, multi-column sorting, `/status` metadata endpoint. |
| **Database** (`:5432`) | PostgreSQL 16 Alpine | Indexed relational database for fast query execution. |

---

## Quickstart

### 1. Launch with Docker Compose
```bash
docker compose up --build
```

### 2. Upload Sample Dataset
```bash
curl -X POST "http://localhost:3000/upload" -F "file=@data/emissions.csv"
```
**Response**:
```json
{
  "message": "File uploaded and processed successfully",
  "details": {
    "message": "CSV file data saved successfully.",
    "summary": {
      "totalRecords": 87500,
      "skippedRows": 0,
      "skippedValues": 0,
      "minEmissions": 0.0,
      "maxEmissions": 14205.32
    }
  }
}
```

### 3. Query the Data
```bash
# Query Spain emissions sorted by year descending
curl "http://localhost:8000/emissions?country=ESP&sort_by=-year&limit=5"

# System metadata & record count
curl http://localhost:8000/status
```

Interactive API documentation is available at **`http://localhost:8000/docs`** (Swagger UI).

---

## API Reference

### 1. Importer Service (`Port 3000`)
- **`GET /health`**: Healthcheck endpoint (`{"status": "ok"}`).
- **`POST /upload`**: Upload CSV file (`multipart/form-data` with field `file`).
  - **Middlewares**: `express.json()`, `Multer`.

### 2. Query Service (`Port 8000`)
- **`GET /health`**: Healthcheck endpoint (`{"status": "ok"}`).
- **`GET /status`**: Returns dataset metadata (`service`, `total_records`, `schema_version`).
- **`GET /emissions`**: Query emissions dataset.

| Query Parameter | Type | Description |
| :--- | :--- | :--- |
| `country`, `sector`, `parent_sector` | `string` | Case-insensitive prefix search. |
| `year` | `integer` | Exact year filter. |
| `value` | `float` | Exact value filter. |
| `page`, `limit` | `integer` | Pagination controls (default: `page=1`; `limit=20`: max `100`). |
| `sort_by` | `string` | Comma-separated fields. Use `-` for DESC (e.g. `country,-year`). Safe column validation applied. |

---

## Design & Performance Decisions

1. **Streaming & Batch Processing**: Node.js streams process CSV rows line-by-line. Records are inserted in batches within SQL transactions to maximize write throughput.
2. **Resource Lifecycle**: `Multer` buffers files which are automatically deleted after processing.
3. **Database Indexing**: Pre-configured B-Tree indexes on `country`, `sector`, `parent_sector`, and `year` eliminate full table scans for sub-millisecond query responses.
4. **Async Non-Blocking API**: Built with FastAPI, AsyncSQLAlchemy, and `asyncpg` to serve high concurrency read requests without blocking the event loop.

---

## Testing & CI/CD

### Local Testing
```bash
# Importer Service (Node.js)
cd importer-service && npm install
npm test      # Vitest unit & integration tests
npm run lint  # ESLint check

# Query Service (Python)
cd query-service && pip install -r requirements.txt
pytest        # Pytest suite
flake8 src    # Flake8 & Black lint check
```

### GitHub Actions CI
Automated pipeline (`.github/workflows/ci.yml`) runs linting, compilation checks, and test suites for both services on every `push` and `pull_request`.

---

## Repository Structure

```
vizzuality-coding-challenge/
├── .github/workflows/ci.yml     # CI pipeline configuration
├── data/emissions.csv          # Sample dataset
├── importer-service/            # Node.js CSV Importer (Express, Drizzle, Vitest)
├── query-service/               # Python Query API (FastAPI, AsyncSQLAlchemy, Pytest)
├── scripts/init.sql             # PostgreSQL schema & B-Tree indexes
├── docker-compose.yml           # Container orchestration
└── .env                         # Environment configuration
```

> **Note on `.env`**: Included directly in repository for ease of evaluation in this coding challenge. In production environments, secrets should be excluded from version control and injected via a secret manager.

---
