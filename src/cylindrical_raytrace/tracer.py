"""Ray tracing through two concentric, zero-thickness circular interfaces."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math

from .geometry import EPSILON, Ray, Vec2, ray_circle_intersections
from .optics import interact


@dataclass(frozen=True)
class CylinderModel:
    inner_radius: float
    outer_radius: float
    n1: float = 1.0
    n2: float = 1.33

    def __post_init__(self) -> None:
        if self.inner_radius <= 0:
            raise ValueError("inner radius must be positive")
        if self.outer_radius <= self.inner_radius:
            raise ValueError("outer radius must be greater than inner radius")
        if self.n1 <= 0 or self.n2 <= 0:
            raise ValueError("refractive indices must be positive")

    def index_at_radius(self, radius: float) -> float:
        return self.n2 if self.inner_radius < radius < self.outer_radius else self.n1


@dataclass(frozen=True)
class Segment:
    start: Vec2
    end: Vec2
    refractive_index: float
    length: float


@dataclass(frozen=True)
class Event:
    number: int
    boundary: str
    action: str
    point: Vec2
    n_from: float
    n_to: float
    incidence_angle_deg: float
    refraction_angle_deg: float | None


@dataclass(frozen=True)
class TraceResult:
    events: list[Event]
    segments: list[Segment]
    termination: str

    @property
    def geometric_length(self) -> float:
        return sum(segment.length for segment in self.segments)

    @property
    def optical_path_length(self) -> float:
        return sum(segment.length * segment.refractive_index for segment in self.segments)

    def to_dict(self) -> dict:
        return {
            "events": [asdict(event) for event in self.events],
            "segments": [asdict(segment) for segment in self.segments],
            "geometric_length": self.geometric_length,
            "optical_path_length": self.optical_path_length,
            "termination": self.termination,
        }


def _region(model: CylinderModel, point: Vec2) -> str:
    radius = point.norm()
    if radius < model.inner_radius:
        return "inner"
    if radius < model.outer_radius:
        return "liquid"
    return "outside"


def _index(model: CylinderModel, region: str) -> float:
    return model.n2 if region == "liquid" else model.n1


def trace_ray(model: CylinderModel, ray: Ray, max_events: int = 20) -> TraceResult:
    if max_events <= 0:
        raise ValueError("max events must be positive")
    current = ray
    region = _region(model, current.origin)
    events: list[Event] = []
    segments: list[Segment] = []

    for number in range(1, max_events + 1):
        candidates: list[tuple[float, str, float]] = []
        for boundary, radius in (("inner", model.inner_radius), ("outer", model.outer_radius)):
            for distance in ray_circle_intersections(current, radius):
                probe = current.at(distance + EPSILON * 100)
                if _region(model, probe) != region:
                    candidates.append((distance, boundary, radius))
                    break
        if not candidates:
            termination = "exited" if region == "outside" else "no further boundary"
            return TraceResult(events, segments, termination)

        distance, boundary, radius = min(candidates)
        point = current.at(distance)
        segments.append(Segment(current.origin, point, _index(model, region), distance))
        outward = point * (1.0 / radius)
        normal = outward if current.direction.dot(outward) < 0 else outward * -1.0
        transmitted_probe = point + current.direction * (EPSILON * 100)
        next_region = _region(model, transmitted_probe)
        n_from, n_to = _index(model, region), _index(model, next_region)
        result = interact(current.direction, normal, n_from, n_to)
        events.append(Event(
            number, boundary, result.action, point, n_from, n_to,
            math.degrees(result.incidence_angle),
            None if result.refraction_angle is None else math.degrees(result.refraction_angle),
        ))
        if result.action == "refract":
            region = next_region
        current = Ray(point + result.direction * (EPSILON * 100), result.direction)

    return TraceResult(events, segments, "max events reached")
