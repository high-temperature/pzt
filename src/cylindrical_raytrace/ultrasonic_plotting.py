"""Plot the PFA tube, finite matching layer, and ultrasonic path."""

from __future__ import annotations

import math
import matplotlib.pyplot as plt
from matplotlib.patches import Arc, Wedge

from .acoustics import AcousticTraceResult, UltrasonicModel
from .geometry import Ray


def save_ultrasonic_plot(model: UltrasonicModel, incoming: Ray,
                         trace: AcousticTraceResult, path: str) -> None:
    figure, axes = plt.subplots()
    axes.add_patch(plt.Circle((0, 0), model.outer_radius_mm, color="#d8d8d8"))
    axes.add_patch(plt.Circle((0, 0), model.inner_radius_mm, color="#9dd9f3"))
    half_deg = math.degrees(model.matching_width_mm / (2 * model.outer_radius_mm))
    center = model.matching_center_angle_deg
    axes.add_patch(Wedge((0, 0), model.matching_outer_radius_mm, center - half_deg,
                         center + half_deg, width=model.matching_thickness_mm,
                         color="#f2c14e", label="matching layer"))
    axes.add_patch(Arc((0, 0), 2 * model.matching_outer_radius_mm,
                       2 * model.matching_outer_radius_mm, theta1=center - half_deg,
                       theta2=center + half_deg, color="black", linewidth=2, label="PZT"))
    points = [incoming.origin] + [segment.end for segment in trace.segments]
    axes.plot([p.x for p in points], [p.y for p in points], "-o", color="#d62728", label="ultrasound")
    extent = model.matching_outer_radius_mm * 1.25
    axes.set(xlim=(-extent, extent), ylim=(-extent, extent), aspect="equal",
             xlabel="x (mm)", ylabel="y (mm)", title="Water / PFA / matching layer")
    axes.legend()
    figure.tight_layout()
    figure.savefig(path)
    plt.close(figure)
