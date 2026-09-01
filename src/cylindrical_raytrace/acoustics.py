"""Ultrasonic ray tracing for a water-filled PFA tube and matching layer."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math

from .geometry import EPSILON, Ray, Vec2, ray_circle_intersections
from .optics import interact


def _angle_delta(a: float, b: float) -> float:
    return (a - b + math.pi) % (2 * math.pi) - math.pi


@dataclass(frozen=True)
class UltrasonicModel:
    """Dimensions are millimetres and sound speeds are metres per second."""

    inner_radius_mm: float
    outer_radius_mm: float
    pfa_speed: float = 1231.0
    water_speed: float = 1497.0
    matching_speed: float = 1046.0
    matching_width_mm: float = 2.0
    matching_thickness_mm: float = 0.5
    matching_center_angle_deg: float = 180.0

    def __post_init__(self) -> None:
        if self.inner_radius_mm <= 0 or self.outer_radius_mm <= self.inner_radius_mm:
            raise ValueError("outer radius must be greater than the positive inner radius")
        if min(self.pfa_speed, self.water_speed, self.matching_speed) <= 0:
            raise ValueError("sound speeds must be positive")
        if self.matching_width_mm <= 0 or self.matching_thickness_mm <= 0:
            raise ValueError("matching-layer dimensions must be positive")
        if self.matching_width_mm > 2 * math.pi * self.outer_radius_mm:
            raise ValueError("matching-layer width cannot exceed the tube circumference")

    @property
    def matching_outer_radius_mm(self) -> float:
        return self.outer_radius_mm + self.matching_thickness_mm

    def in_matching_arc(self, point: Vec2) -> bool:
        angle = math.atan2(point.y, point.x)
        center = math.radians(self.matching_center_angle_deg)
        half_angle = self.matching_width_mm / (2 * self.outer_radius_mm)
        return abs(_angle_delta(angle, center)) <= half_angle + 1e-12


@dataclass(frozen=True)
class AcousticSegment:
    start: Vec2
    end: Vec2
    medium: str
    sound_speed_m_s: float
    length_mm: float

    @property
    def travel_time_us(self) -> float:
        return self.length_mm * 1000.0 / self.sound_speed_m_s


@dataclass(frozen=True)
class AcousticEvent:
    number: int
    boundary: str
    action: str
    point: Vec2
    from_medium: str
    to_medium: str | None
    incidence_angle_deg: float
    transmission_angle_deg: float | None


@dataclass(frozen=True)
class AcousticTraceResult:
    events: list[AcousticEvent]
    segments: list[AcousticSegment]
    termination: str

    @property
    def travel_time_us(self) -> float:
        return sum(segment.travel_time_us for segment in self.segments)

    def to_dict(self) -> dict:
        return {
            "events": [asdict(event) for event in self.events],
            "segments": [{**asdict(segment), "travel_time_us": segment.travel_time_us}
                         for segment in self.segments],
            "travel_time_us": self.travel_time_us,
            "termination": self.termination,
        }


def _medium(model: UltrasonicModel, point: Vec2) -> str:
    radius = point.norm()
    if radius < model.inner_radius_mm:
        return "water"
    if radius < model.outer_radius_mm:
        return "pfa"
    if radius < model.matching_outer_radius_mm and model.in_matching_arc(point):
        return "matching"
    return "air"


def _speed(model: UltrasonicModel, medium: str) -> float:
    return {"water": model.water_speed, "pfa": model.pfa_speed,
            "matching": model.matching_speed}[medium]


def trace_ultrasound(model: UltrasonicModel, ray: Ray, max_events: int = 30) -> AcousticTraceResult:
    """Trace a ray; PFA exposed to air reflects perfectly and PZT absorbs the ray."""
    if max_events <= 0:
        raise ValueError("max events must be positive")
    current, medium = ray, _medium(model, ray.origin)
    if medium == "air":
        raise ValueError("origin must be in water, PFA, or the matching layer")
    events: list[AcousticEvent] = []
    segments: list[AcousticSegment] = []
    radii = (("water-pfa", model.inner_radius_mm),
             ("pfa-outer", model.outer_radius_mm),
             ("matching-pzt", model.matching_outer_radius_mm))

    for number in range(1, max_events + 1):
        candidates: list[tuple[float, str, float, str]] = []
        for boundary, radius in radii:
            for distance in ray_circle_intersections(current, radius):
                point = current.at(distance)
                after = _medium(model, current.at(distance + EPSILON * 100))
                if after != medium:
                    candidates.append((distance, boundary, radius, after))
                    break
        if not candidates:
            return AcousticTraceResult(events, segments, "no further boundary")

        distance, boundary, radius, after = min(candidates)
        point = current.at(distance)
        segments.append(AcousticSegment(current.origin, point, medium, _speed(model, medium), distance))
        outward = point * (1 / radius)
        normal = outward if current.direction.dot(outward) < 0 else outward * -1
        incidence = math.degrees(math.acos(max(0.0, min(1.0, -current.direction.dot(normal)))))

        if boundary == "matching-pzt" and medium == "matching":
            events.append(AcousticEvent(number, boundary, "received", point, medium, "pzt", incidence, None))
            return AcousticTraceResult(events, segments, "reached PZT")

        if after == "air":
            direction = current.direction + normal * (2 * -current.direction.dot(normal))
            action, next_medium, transmission = "reflect", medium, None
        else:
            # Acoustic Snell law: sin(theta)/speed is conserved, hence optical n=1/speed.
            result = interact(current.direction, normal, 1 / _speed(model, medium), 1 / _speed(model, after))
            direction, action = result.direction, result.action
            next_medium = after if action == "refract" else medium
            transmission = None if result.refraction_angle is None else math.degrees(result.refraction_angle)
        events.append(AcousticEvent(number, boundary, action, point, medium,
                                    None if after == "air" else after, incidence, transmission))
        medium = next_medium
        current = Ray(point + direction * (EPSILON * 100), direction)

    return AcousticTraceResult(events, segments, "max events reached")
