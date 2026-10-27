
import os
import time
import logging
from docker.errors import DockerException
from logging.handlers import RotatingFileHandler

from app.metrics import get_resource_usage
from app.docker_client import client
from app.alerts import (
    check_container_status,
    check_resource_alerts,
    cleanup_alert_tracking,
    CPU_THRESHOLD,
    MEMORY_THRESHOLD,
)

CHECK_INTERVAL = 10

os.makedirs("logs", exist_ok=True)

handler = RotatingFileHandler(
    "logs/monitor.log",
    maxBytes=1_000_000,
    backupCount=3,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[handler],
)


def check_containers():
    containers = client.containers.list(all=True)
    current_container_ids = set()

    for container in containers:
        try:
            container.reload()

            status = container.status
            container_id = container.id
            current_container_ids.add(container_id)

            print(f"Name: {container.name}")
            print(f"Status: {status}")

            check_container_status(container)

            if status == "running":
                print(f"INFO: {container.name} is running.")
                logging.info(f"INFO: {container.name} is running.")

                try:
                    cpu, memory, memory_percent = get_resource_usage(
                        container
                    )

                    print(f"CPU Usage: {cpu:.2f}%")
                    print(f"Memory Usage: {memory / (1024 ** 2):.2f} MiB")
                    print(f"Memory Usage: {memory_percent:.2f}%")

                    check_resource_alerts(
                        container,
                        cpu,
                        memory_percent,
                    )

                except (KeyError, ZeroDivisionError, ValueError) as error:
                    message = (
                        f"Could not read resource metrics for "
                        f"{container.name}: {error}"
                    )
                    print(message)
                    logging.error(message)

                except DockerException as error:
                    message = (
                        f"Could not retrieve stats for "
                        f"{container.name}: {error}"
                    )
                    print(message)
                    logging.error(message)

            elif status != "exited":
                message = f"INFO: Container state is {status}."
                print(message)
                logging.info(message)

            print("-" * 30)

        except DockerException as error:
            message = (
                f"Could not inspect container {container.name}: {error}"
            )
            print(message)
            logging.error(message)

    cleanup_alert_tracking(current_container_ids)


def start_monitoring():
    print("Docker monitoring started...")
    print(f"Checking containers every {CHECK_INTERVAL} seconds.")
    print(f"CPU threshold: {CPU_THRESHOLD}%")
    print(f"Memory threshold: {MEMORY_THRESHOLD}%")
    print("Press Ctrl+C to stop.\n")

    while True:
        try:
            check_containers()
            time.sleep(CHECK_INTERVAL)

        except DockerException as error:
            message = f"Docker connection error: {error}"
            print(message)
            logging.error(message)
            time.sleep(CHECK_INTERVAL)

        except KeyboardInterrupt:
            print("\nMonitoring stopped.")
            break


if __name__ == "__main__":
    start_monitoring()
