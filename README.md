# 🐳 Docker Container Health Monitor

<p align="center">
  <strong>A lightweight Python tool to monitor Docker container health, CPU and memory usage.</strong>
  <br />
  REST API + background monitor + threshold alerts + rotating logs, all packaged in one Docker image.
</p>

<p align="center">
  <a href="https://github.com/Maniraj-CS/docker-health-monitor/actions/workflows/ci.yml">
    <img src="https://github.com/Maniraj-CS/docker-health-monitor/actions/workflows/ci.yml/badge.svg" alt="CI status" />
  </a>
  <img src="https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-REST%20API-009688?logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Docker-Containerized-2496ED?logo=docker&logoColor=white" alt="Docker" />
  <img src="https://img.shields.io/badge/Tests-pytest-0A9EDC?logo=pytest&logoColor=white" alt="pytest" />
</p>

---

## 📖 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Demo](#-demo)
- [Architecture](#️-architecture)
- [Quick Start](#-quick-start)
- [Run Locally (without Docker)](#-run-locally-without-docker)
- [API Endpoints](#-api-endpoints)
- [Alerts](#-alerts)
- [Logging](#-logging-and-log-rotation)
- [Makefile Commands](#️-makefile-commands)
- [Testing](#-testing)
- [Project Structure](#-project-structure)
- [Security Considerations](#-security-considerations)
- [Roadmap](#️-roadmap)
- [Author](#-author)

## 📌 Overview

Docker Container Health Monitor watches the containers running on a Docker host and keeps track of their status and resource usage.

- A **FastAPI** service exposes container details and live CPU/memory metrics.
- A **background monitor** checks every container every 10 seconds and logs alerts when a container stops or when CPU or memory usage crosses a threshold.
- Alerts are **de-duplicated** (no spam on consecutive cycles) and a **recovery** message is logged when things return to normal.

Both processes run together inside a single Docker image, and the container only needs access to the Docker socket.

## ✨ Features

| | Feature | Description |
|---|---|---|
| 🟢 | **Container monitoring** | Tracks running and stopped containers |
| 📊 | **Resource metrics** | CPU and memory usage per container |
| 🚨 | **Threshold alerts** | `WARNING` when CPU or memory exceeds 80% |
| 🔄 | **Recovery alerts** | `INFO` when a container or its resource usage returns to normal |
| 🔁 | **Duplicate alert prevention** | The same alert is not repeated in consecutive cycles |
| 🌐 | **REST API** | Container list and stats via FastAPI, with Swagger docs |
| 📝 | **Logging** | Console + file logging |
| 📦 | **Log rotation** | Rotates at 1 MB, keeps 3 backups |
| 🐳 | **Dockerized** | API and monitor packaged together |
| 🛠️ | **Makefile** | One-line build, run, logs, stop, clean, and test |
| 🧪 | **Automated tests** | pytest suite, run automatically in GitHub Actions CI |


## 🏗️ Architecture


<p align="center">
  <img src="./assets/architecture (3).svg" alt="Docker Health Monitor architecture" width="900" />
</p>


## 🚀 Quick Start

The fastest way to try it is with Docker.

**Requirements:** Docker Engine, Git, GNU Make.

```bash
# 1. Clone
git clone https://github.com/Maniraj-CS/docker-health-monitor.git
cd docker-health-monitor

# 2. Build the image
make build

# 3. Run (logs are saved to ./logs by default)
make run
```

Then open:

- API root: http://127.0.0.1:8000/
- Swagger docs: http://127.0.0.1:8000/docs

Useful follow-ups:

```bash
make logs            # follow container console output
tail -f logs/monitor.log   # follow the monitor log file on the host
make stop            # stop and remove the container
```

To save logs in a custom folder (created automatically if missing):

```bash
make run LOG_DIR=/home/maniraj/docker-logs
```

> **Note:** `make run` uses the fixed container name `health-monitor`. If a container with that name already exists, run `make clean` first.

### Try it out

Start a test container, stop it, and start it again to see the alerts appear in the log:

```bash
docker run -d --name test-nginx nginx
docker stop test-nginx      # -> container stopped WARNING
docker start test-nginx     # -> recovery INFO
tail -f logs/monitor.log
```

## 💻 Run Locally (without Docker)

**Requirements:** Python 3.12+, Docker Engine access (the user must be able to talk to the Docker daemon).

```bash
git clone https://github.com/Maniraj-CS/docker-health-monitor.git
cd docker-health-monitor

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Start the API:

```bash
uvicorn app.main:app --reload
```

In a second terminal (with the virtual environment activated), start the monitor:

```bash
python -m app.monitor
```

> On Linux, access to the Docker daemon usually depends on Docker socket permissions.

## 🌐 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | API status check |
| `GET` | `/containers` | List Docker containers |
| `GET` | `/containers/{container_name}/stats` | Resource metrics for a running container |

**List containers**

```bash
curl http://127.0.0.1:8000/containers
```

**Get container stats** (replace `my-container` with a running container's name)

```bash
curl http://127.0.0.1:8000/containers/my-container/stats
```

Example response (values are illustrative):

```json
{
  "name": "my-container",
  "status": "running",
  "cpu_percent": 12.5,
  "memory_usage_mib": 64.25,
  "memory_percent": 8.4
}
```

## 🚨 Alerts

Default thresholds are defined in `app/alerts.py`:

```python
CPU_THRESHOLD = 80.0
MEMORY_THRESHOLD = 80.0
```

| Condition | Log level |
|---|---|
| Container stopped | `WARNING` |
| CPU usage exceeds threshold | `WARNING` |
| Memory usage exceeds threshold | `WARNING` |
| Container or resource usage recovered | `INFO` |

The monitor checks all containers every **10 seconds**. An alert is logged once when a condition starts, not on every cycle.

## 📝 Logging and Log Rotation

Logs are written to the console and to `logs/monitor.log`.

| Setting | Value |
|---|---|
| Max file size | 1 MB |
| Backup files | 3 |
| Levels | `INFO`, `WARNING`, `ERROR` |

When running with Docker, the log directory is mounted from the host, so logs stay available even after the container is removed.

## 🛠️ Makefile Commands

| Command | Description |
|---|---|
| `make build` | Build the Docker image |
| `make run` | Start the container (default log directory) |
| `make run LOG_DIR=/path/to/logs` | Start the container with a custom log directory |
| `make logs` | Follow the container's console logs |
| `make stop` | Stop and remove the container |
| `make clean` | Force-remove the container |
| `make test` | Run the pytest test suite |

## 🧪 Testing

```bash
make test
# or
python -m pytest -v
```

The suite covers API responses, Docker errors, threshold alerts, recovery alerts, and duplicate alert prevention. Tests also run automatically on every push through GitHub Actions (see the CI badge at the top).

## 📂 Project Structure

```text
docker-health-monitor/
├── app/
│   ├── __init__.py
│   ├── main.py            # FastAPI app and endpoints
│   ├── monitor.py         # Background monitoring loop
│   ├── metrics.py         # CPU and memory calculation
│   ├── docker_client.py   # Docker SDK wrapper
│   └── alerts.py          # Thresholds and alert logic
├── tests/
│   ├── test_api.py
│   └── test_monitor.py
├── logs/
│   └── monitor.log
├── .github/
│   └── workflows/
│       └── ci.yml
├── .dockerignore
├── Dockerfile
├── start.sh
├── Makefile
├── requirements.txt
├── README.md
└── .gitignore
```

## 🔐 Security Considerations

- **Docker socket access:** Mounting `/var/run/docker.sock` gives the application powerful control over the host's Docker daemon. Only run it in environments you trust.
- **API exposure:** The API has no authentication. Do not expose it to the public internet without adding authentication and network restrictions.
- **Secrets:** Never commit credentials or sensitive configuration to the repository.
- **Log permissions:** Make sure the host log directory has appropriate permissions.

## 🗺️ Roadmap

**Completed**

- [x] Container status monitoring
- [x] CPU and memory monitoring
- [x] Threshold and recovery alerts
- [x] FastAPI endpoints
- [x] Automated tests
- [x] Rotating file logging
- [x] Dockerfile and startup script
- [x] Makefile
- [x] `.dockerignore`
- [x] GitHub Actions CI workflow

**In progress**

- [ ] Final end-to-end testing and documentation review

**Ideas for the future**

- [ ] Configurable thresholds and check interval through environment variables
- [ ] Webhook / Slack / email notifications
- [ ] Docker `HEALTHCHECK` and a `/health` endpoint
- [ ] Prometheus `/metrics` endpoint for Grafana dashboards
- [ ] API authentication

## 🧰 Tech Stack

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![Pytest](https://img.shields.io/badge/Pytest-0A9EDC?style=flat-square&logo=pytest&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-2088FF?style=flat-square&logo=githubactions&logoColor=white)
![Make](https://img.shields.io/badge/Makefile-000000?style=flat-square&logo=gnu&logoColor=white)

## 👨‍💻 Author

**Maniraj Pandit**

- GitHub: [@Maniraj-CS](https://github.com/Maniraj-CS)

---

<p align="center">
  <sub>Built to practise Python, Docker, monitoring, logging, REST APIs, and DevOps fundamentals.</sub>
</p>