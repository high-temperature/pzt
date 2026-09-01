"""Reflection and refraction at an ideal optical interface."""

from __future__ import annotations

from dataclasses import dataclass
import math

from .geometry import Vec2


@dataclass(frozen=True)
class InterfaceResult:
    direction: Vec2
    action: str
    incidence_angle: float
    refraction_angle: float | None


def interact(direction: Vec2, normal_to_incident: Vec2, n_from: float, n_to: float) -> InterfaceResult:
    """Apply Snell's law; the normal must point into the incident medium."""
    direction = direction.normalized()
    normal = normal_to_incident.normalized()
    cos_incident = max(0.0, min(1.0, -direction.dot(normal)))
    incidence = math.acos(cos_incident)
    ratio = n_from / n_to
    sin_transmitted_sq = ratio * ratio * max(0.0, 1.0 - cos_incident * cos_incident)
    if sin_transmitted_sq > 1.0 + 1e-12:
        reflected = direction + normal * (2.0 * cos_incident)
        return InterfaceResult(reflected.normalized(), "reflect", incidence, None)
    cos_transmitted = math.sqrt(max(0.0, 1.0 - sin_transmitted_sq))
    transmitted = direction * ratio + normal * (ratio * cos_incident - cos_transmitted)
    return InterfaceResult(
        transmitted.normalized(),
        "refract",
        incidence,
        math.asin(min(1.0, math.sqrt(sin_transmitted_sq))),
    )
