
from fastapi import FastAPI, HTTPException
from docker.errors import DockerException, NotFound

from app.docker_client import client
from app.metrics import get_resource_usage


app = FastAPI(title="Docker Container Health Monitor")


@app.get("/")
def home():
    return {
        "message": "Docker Container Health Monitor API",
        "status": "running",
    }


@app.get("/containers")
def list_containers():
    try:
        containers = client.containers.list(all=True)

        result = []

        for container in containers:
            result.append({
                "name": container.name,
                "id": container.short_id,
                "status": container.status,
            })

        return {"containers": result}

    except DockerException as error:
        raise HTTPException(
            status_code=503,
            detail=f"Docker is unavailable: {error}",
        ) from error


@app.get("/containers/{container_name}/stats")
def container_stats(container_name: str):
    try:
        container = client.containers.get(container_name)
        container.reload()

        if container.status != "running":
            raise HTTPException(
                status_code=409,
                detail="Container is not running",
            )

        cpu, memory, memory_percent = get_resource_usage(container)

        return {
            "name": container.name,
            "status": container.status,
            "cpu_percent": round(cpu, 2),
            "memory_usage_mib": round(memory / (1024 ** 2), 2),
            "memory_percent": round(memory_percent, 2),
        }

    except NotFound as error:
        raise HTTPException(
            status_code=404,
            detail="Container not found",
        ) from error

    except DockerException as error:
        raise HTTPException(
            status_code=503,
            detail="Could not retrieve container information.",
        ) from error
