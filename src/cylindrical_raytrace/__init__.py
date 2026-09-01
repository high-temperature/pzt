"""Two-dimensional ray tracing for concentric cylindrical boundaries."""

from .geometry import Ray, Vec2
from .tracer import CylinderModel, TraceResult, trace_ray

__version__ = "0.1.1"

__all__ = ["CylinderModel", "Ray", "TraceResult", "Vec2", "trace_ray"]
