from __future__ import annotations

from .models import Task


class PlanError(ValueError):
    pass


def build_execution_levels(tasks: list[Task]) -> list[list[Task]]:
    (
        task_by_name,
        adjacency,
        in_degree,
        position,
    ) = _build_dependency_graph(tasks)

    ready = [task.name for task in tasks if in_degree[task.name] == 0]
    levels: list[list[Task]] = []
    seen = 0

    while ready:
        current_level = sorted(ready, key=position.get)
        levels.append([task_by_name[name] for name in current_level])
        seen += len(current_level)

        next_ready: list[str] = []
        for current in current_level:
            for child in adjacency[current]:
                in_degree[child] -= 1
                if in_degree[child] == 0:
                    next_ready.append(child)
        ready = next_ready

    if seen != len(tasks):
        unresolved = [name for name, degree in in_degree.items() if degree > 0]
        raise PlanError(f"cycle detected in plan: {', '.join(unresolved)}")

    return levels


def build_execution_order(tasks: list[Task]) -> list[Task]:
    return [task for level in build_execution_levels(tasks) for task in level]


def build_mermaid_graph(tasks: list[Task]) -> str:
    # Ensure the graph is valid before emitting visualization.
    build_execution_levels(tasks)

    node_ids = {task.name: f"T{idx + 1}" for idx, task in enumerate(tasks)}
    lines = ["graph TD"]

    for task in tasks:
        node_id = node_ids[task.name]
        label = task.name.replace('"', "'")
        lines.append(f'  {node_id}["{label}"]')

    for task in tasks:
        for dep in task.after:
            lines.append(f"  {node_ids[dep]} --> {node_ids[task.name]}")

    return "\n".join(lines)


def _build_dependency_graph(
    tasks: list[Task],
) -> tuple[dict[str, Task], dict[str, list[str]], dict[str, int], dict[str, int]]:
    task_by_name = {task.name: task for task in tasks}
    if len(task_by_name) != len(tasks):
        raise PlanError("duplicate task names found in plan")

    adjacency: dict[str, list[str]] = {task.name: [] for task in tasks}
    in_degree: dict[str, int] = {task.name: 0 for task in tasks}
    position = {task.name: idx for idx, task in enumerate(tasks)}

    for task in tasks:
        for dep in task.after:
            if dep not in task_by_name:
                raise PlanError(
                    f"task '{task.name}' depends on unknown task '{dep}'"
                )
            adjacency[dep].append(task.name)
            in_degree[task.name] += 1

    return task_by_name, adjacency, in_degree, position
