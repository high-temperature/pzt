"""Command-line interface for the cylindrical ray tracer."""

from __future__ import annotations

import argparse
import json
import math
import sys

from .geometry import Ray, Vec2
from .tracer import CylinderModel, trace_ray
from . import __version__


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Trace a ray through concentric cylindrical boundaries.")
    result.add_argument("--version", action="version", version=f"cylindrical-raytrace {__version__}")
    result.add_argument("--inner-radius", type=float, required=True)
    result.add_argument("--outer-radius", type=float, required=True)
    result.add_argument("--n1", type=float, default=1.0, help="index outside and inside the inner cylinder")
    result.add_argument("--n2", type=float, required=True, help="liquid absolute refractive index")
    result.add_argument("--origin-x", type=float, required=True)
    result.add_argument("--origin-y", type=float, required=True)
    result.add_argument("--angle-deg", type=float, required=True)
    result.add_argument("--max-events", type=int, default=20)
    result.add_argument("--output-format", choices=("table", "json"), default="table")
    result.add_argument("--plot", metavar="PATH", help="save a PNG/SVG ray-path plot (requires matplotlib)")
    return result


def _table(trace) -> str:
    lines = [
        "event boundary action          x          y   n_from     n_to incidence refraction",
        "----- -------- ------- ---------- ---------- -------- -------- --------- ----------",
    ]
    for event in trace.events:
        refraction = "-" if event.refraction_angle_deg is None else f"{event.refraction_angle_deg:.4f}°"
        lines.append(
            f"{event.number:5d} {event.boundary:8s} {event.action:7s} "
            f"{event.point.x:10.5f} {event.point.y:10.5f} {event.n_from:8.4f} "
            f"{event.n_to:8.4f} {event.incidence_angle_deg:8.4f}° {refraction:>10s}"
        )
    lines.extend((
        f"Geometric path length: {trace.geometric_length:.8g}",
        f"Optical path length: {trace.optical_path_length:.8g}",
        f"Termination: {trace.termination}",
    ))
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        model = CylinderModel(args.inner_radius, args.outer_radius, args.n1, args.n2)
        angle = math.radians(args.angle_deg)
        ray = Ray(Vec2(args.origin_x, args.origin_y), Vec2(math.cos(angle), math.sin(angle)))
        trace = trace_ray(model, ray, args.max_events)
        if args.plot:
            from .plotting import save_plot

            save_plot(model, ray, trace, args.plot)
    except (ValueError, RuntimeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(json.dumps(trace.to_dict(), indent=2) if args.output_format == "json" else _table(trace))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
