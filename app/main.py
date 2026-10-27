from fastapi import FastAPI, HTTPException
from docker.errors import DockerException, NotFound
from app.metrics import get_resource_usage
from app.docker_client import client


app = FastAPI(title="Docker Container Health Monitor")

def monitor_containers():
    containers = client.containers.list(all=True)

    for container in containers:

        container_status = container.status

        print(f"Name: {container.name}")
        print(f"Status: {container_status}")
        print(f"Id: {container.short_id}")

        if container_status == "running" : 
            try:
              cpu , memory , memory_percent =  get_resource_usage(container)

              print(f"CPU Usage: {cpu:.2f}%")
              print(f"Memory Usage: {memory / (1024 ** 2):.2f} MiB")
              print(f"Memory Limit: {memory_percent:.2f}%")

            except (KeyError , ZeroDivisionError) as error:
                print(f"Could not read resource metrics: {error}")
 
            
        elif container_status == "exited":
            print("ALERT: Container has stopped ")
        else:
            print(f"INFO: Container state is {container_status}")

        print("-"*30)



@app.get("/")
def home():
    return {
        "message": "Docker Container Health Monitor API",
        "status": "running"
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
                "status": container.status
            })

        return {"containers": result}

    except DockerException as error:
        raise HTTPException(
            status_code=503,
            detail=f"Docker is unavailable: {error}"
        )


@app.get("/containers/{container_name}/stats")
def container_stats(container_name: str):
    try:
        container = client.containers.get(container_name)
        container.reload()

        if container.status != "running":
            raise HTTPException(
                status_code=409,
                detail="Container is not running"
            )

        cpu, memory, memory_percent = get_resource_usage(container)

        return {
            "name": container.name,
            "status": container.status,
            "cpu_percent": round(cpu, 2),
            "memory_usage_mib": round(memory / (1024 ** 2), 2),
            "memory_percent": round(memory_percent, 2)
        }

    except NotFound as error:
        raise HTTPException(
            status_code=404,
            detail="Container not found"
        ) from error

    except DockerException as error:
        raise HTTPException(
            status_code=503,
            detail="Could not retrieve container information."
        ) from error

if __name__ == "__main__":
    monitor_containers()
