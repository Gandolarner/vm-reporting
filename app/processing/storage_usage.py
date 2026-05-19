def calculate_storage_usage_percent(
    disks: list[dict],
) -> float | None:
    """
    Calculate storage usage percentage
    from guest disk data.
    """

    if not disks:
        return None

    total_capacity = 0
    total_used = 0

    for disk in disks:
        capacity = disk.get("capacity") or 0
        free_space = disk.get("free_space") or 0

        if capacity <= 0:
            continue

        used_space = capacity - free_space

        total_capacity += capacity
        total_used += used_space

    if total_capacity == 0:
        return None

    return total_used / total_capacity * 100