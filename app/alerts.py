import logging

CPU_THRESHOLD = 80.0
MEMORY_THRESHOLD = 80.0

alerted_containers = set()
high_cpu_alerted = set()
high_memory_alerted = set()


def check_container_status(container):
    container_id = container.id
    name = container.name
    status = container.status

    if status == "exited":
        if container_id not in alerted_containers:
            message = f"ALERT: {name} has stopped!"
            print(message)
            logging.warning(message)
            alerted_containers.add(container_id)

        else:
            print("INFO: Stop alert already sent.")

    elif status == "running":
        if container_id in alerted_containers:
            message = f"RECOVERED: {name} is running again!"
            print(message)
            logging.info(message)
            alerted_containers.remove(container_id)


def check_resource_alerts(container, cpu, memory_percent):
    container_id = container.id
    name = container.name

    # CPU threshold alert
    if cpu > CPU_THRESHOLD:
        if container_id not in high_cpu_alerted:
            message = (
                f"ALERT: {name} CPU usage is high: {cpu:.2f}%"
            )
            print(message)
            logging.warning(message)
            high_cpu_alerted.add(container_id)

    elif container_id in high_cpu_alerted:
        message = (
            f"RECOVERED: {name} CPU usage is back to normal: "
            f"{cpu:.2f}%"
        )
        print(message)
        logging.info(message)
        high_cpu_alerted.remove(container_id)

    # Memory threshold alert
    if memory_percent > MEMORY_THRESHOLD:
        if container_id not in high_memory_alerted:
            message = (
                f"ALERT: {name} memory usage is high: "
                f"{memory_percent:.2f}%"
            )
            print(message)
            logging.warning(message)
            high_memory_alerted.add(container_id)

    elif container_id in high_memory_alerted:
        message = (
            f"RECOVERED: {name} memory usage is back to normal: "
            f"{memory_percent:.2f}%"
        )
        print(message)
        logging.info(message)
        high_memory_alerted.remove(container_id)


def cleanup_alert_tracking(current_container_ids):
    alerted_containers.intersection_update(current_container_ids)
    high_cpu_alerted.intersection_update(current_container_ids)
    high_memory_alerted.intersection_update(current_container_ids)