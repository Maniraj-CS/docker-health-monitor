def get_resource_usage(container):
    stats = container.stats(stream=False)

    # CPU usage
    cpu_stats = stats["cpu_stats"]
    precpu_stats = stats["precpu_stats"]

    cpu_delta = (
        cpu_stats["cpu_usage"]["total_usage"]
        - precpu_stats["cpu_usage"]["total_usage"]
    )

    system_delta = (
        cpu_stats.get("system_cpu_usage", 0)
        - precpu_stats.get("system_cpu_usage", 0)
    )

    cpu_count = cpu_stats.get(
        "online_cpus",
        len(cpu_stats["cpu_usage"].get("percpu_usage", [1]))
    )

    if system_delta > 0 and cpu_delta >= 0:
        cpu_percent = (cpu_delta / system_delta) * cpu_count * 100
    else:
        cpu_percent = 0.0

    # Memory usage
    memory_stats = stats["memory_stats"]
    memory_usage = memory_stats.get("usage", 0)
    memory_limit = memory_stats.get("limit", 0)

    if memory_limit > 0:
        memory_percent = (memory_usage / memory_limit) * 100
    else:
        memory_percent = 0.0

    return cpu_percent, memory_usage, memory_percent