"""Small, dependency-free two-dimensional geometry primitives."""

from __future__ import annotations

from dataclasses import dataclass
import math


EPSILON = 1e-10


@dataclass(frozen=True)
class Vec2:
    x: float
    y: float

    def __add__(self, other: "Vec2") -> "Vec2":
        return Vec2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: "Vec2") -> "Vec2":
        return Vec2(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> "Vec2":
        return Vec2(self.x * scalar, self.y * scalar)

    __rmul__ = __mul__

    def dot(self, other: "Vec2") -> float:
        return self.x * other.x + self.y * other.y

    def norm(self) -> float:
        return math.hypot(self.x, self.y)

    def normalized(self) -> "Vec2":
        length = self.norm()
        if length <= EPSILON:
            raise ValueError("direction vector must not be zero")
        return self * (1.0 / length)


@dataclass(frozen=True)
class Ray:
    origin: Vec2
    direction: Vec2

    def __post_init__(self) -> None:
        object.__setattr__(self, "direction", self.direction.normalized())

    def at(self, distance: float) -> Vec2:
        return self.origin + self.direction * distance


def ray_circle_intersections(ray: Ray, radius: float, epsilon: float = EPSILON) -> list[float]:
    """Return forward distances from *ray* to a circle centred at the origin."""
    projection = ray.origin.dot(ray.direction)
    constant = ray.origin.dot(ray.origin) - radius * radius
    discriminant = projection * projection - constant
    if discriminant < -epsilon:
        return []
    root = math.sqrt(max(0.0, discriminant))
    values = {-projection - root, -projection + root}
    return sorted(value for value in values if value > epsilon)
