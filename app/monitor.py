
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

file_handler = RotatingFileHandler(
    "logs/monitor.log",
    maxBytes=1_000_000,
    backupCount=3,
)

console_handler = logging.StreamHandler()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[console_handler, file_handler],
)

logger = logging.getLogger(__name__)


def check_containers():
    containers = client.containers.list(all=True)
    current_container_ids = set()

    for container in containers:
        try:
            container.reload()

            status = container.status
            container_id = container.id
            current_container_ids.add(container_id)

            logger.info(
                "Container: %s | Status: %s",
                container.name,
                status,
            )

            check_container_status(container)

            if status == "running":
                try:
                    cpu, memory, memory_percent = get_resource_usage(
                        container
                    )

                    logger.info(
                        "Container: %s | CPU: %.2f%% | Memory: %.2f MiB "
                        "(%.2f%%)",
                        container.name,
                        cpu,
                        memory / (1024 ** 2),
                        memory_percent,
                    )

                    check_resource_alerts(
                        container,
                        cpu,
                        memory_percent,
                    )

                except (KeyError, ZeroDivisionError, ValueError) as error:
                    logger.error(
                        "Could not read resource metrics for %s: %s",
                        container.name,
                        error,
                    )

                except DockerException:
                    logger.exception(
                        "Could not retrieve stats for %s",
                        container.name,
                    )

            elif status != "exited":
                logger.info(
                    "Container %s is in state: %s",
                    container.name,
                    status,
                )

        except DockerException:
            logger.exception(
                "Could not inspect container %s",
                container.name,
            )

    cleanup_alert_tracking(current_container_ids)


def start_monitoring():
    logger.info("Docker monitoring started.")
    logger.info("Check interval: %s seconds", CHECK_INTERVAL)
    logger.info("CPU threshold: %s%%", CPU_THRESHOLD)
    logger.info("Memory threshold: %s%%", MEMORY_THRESHOLD)
    logger.info("Press Ctrl+C to stop monitoring.")

    while True:
        try:
            check_containers()
            time.sleep(CHECK_INTERVAL)

        except DockerException:
            logger.exception("Docker connection error.")
            time.sleep(CHECK_INTERVAL)

        except KeyboardInterrupt:
            logger.info("Monitoring stopped.")
            break


if __name__ == "__main__":
    start_monitoring()
