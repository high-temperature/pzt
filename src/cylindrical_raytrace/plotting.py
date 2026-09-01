"""Optional matplotlib output."""

from __future__ import annotations

import matplotlib.pyplot as plt

from .geometry import Ray
from .tracer import CylinderModel, TraceResult


def save_plot(model: CylinderModel, incoming: Ray, trace: TraceResult, path: str) -> None:
    figure, axes = plt.subplots()
    liquid = plt.Circle((0, 0), model.outer_radius, color="#b9e3f5", alpha=0.45)
    core = plt.Circle((0, 0), model.inner_radius, color="white")
    axes.add_patch(liquid)
    axes.add_patch(core)
    for radius in (model.inner_radius, model.outer_radius):
        axes.add_patch(plt.Circle((0, 0), radius, fill=False, color="black"))
    points = [incoming.origin] + [segment.end for segment in trace.segments]
    if points:
        axes.plot([point.x for point in points], [point.y for point in points], "-o", color="#d62728")
    extent = max(model.outer_radius * 1.25, *(abs(value) for point in points for value in (point.x, point.y)))
    axes.set(xlim=(-extent, extent), ylim=(-extent, extent), aspect="equal",
             title=f"n1={model.n1:g}, n2={model.n2:g}", xlabel="x", ylabel="y")
    figure.tight_layout()
    figure.savefig(path)
    plt.close(figure)
