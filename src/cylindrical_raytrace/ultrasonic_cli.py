"""CLI for the water/PFA/matching-layer ultrasonic model."""

from __future__ import annotations

import argparse
import json
import math
import sys

from . import __version__
from .acoustics import UltrasonicModel, trace_ultrasound
from .geometry import Ray, Vec2


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Trace ultrasound in a water-filled PFA tube.")
    result.add_argument("--version", action="version", version=f"ultrasonic-raytrace {__version__}")
    result.add_argument("--inner-radius-mm", type=float, required=True)
    result.add_argument("--outer-radius-mm", type=float, required=True)
    result.add_argument("--origin-x-mm", type=float, required=True)
    result.add_argument("--origin-y-mm", type=float, required=True)
    result.add_argument("--angle-deg", type=float, required=True)
    result.add_argument("--pfa-speed", type=float, default=1231.0)
    result.add_argument("--water-speed", type=float, default=1497.0)
    result.add_argument("--matching-speed", type=float, default=1046.0)
    result.add_argument("--matching-width-mm", type=float, default=2.0)
    result.add_argument("--matching-thickness-mm", type=float, default=0.5)
    result.add_argument("--matching-center-angle-deg", type=float, default=180.0)
    result.add_argument("--max-events", type=int, default=30)
    result.add_argument("--output-format", choices=("table", "json"), default="table")
    result.add_argument("--plot", metavar="PATH")
    return result


def _table(trace) -> str:
    lines = ["event boundary       action       x(mm)      y(mm) from      to        incidence transmission"]
    for event in trace.events:
        transmitted = "-" if event.transmission_angle_deg is None else f"{event.transmission_angle_deg:.3f}°"
        lines.append(f"{event.number:5d} {event.boundary:14s} {event.action:9s} "
                     f"{event.point.x:10.4f} {event.point.y:10.4f} {event.from_medium:9s} "
                     f"{(event.to_medium or '-'):9s} {event.incidence_angle_deg:8.3f}° {transmitted:>11s}")
    lines.append(f"Travel time: {trace.travel_time_us:.6f} us")
    lines.append(f"Termination: {trace.termination}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        model = UltrasonicModel(
            args.inner_radius_mm, args.outer_radius_mm, args.pfa_speed, args.water_speed,
            args.matching_speed, args.matching_width_mm, args.matching_thickness_mm,
            args.matching_center_angle_deg,
        )
        angle = math.radians(args.angle_deg)
        ray = Ray(Vec2(args.origin_x_mm, args.origin_y_mm), Vec2(math.cos(angle), math.sin(angle)))
        trace = trace_ultrasound(model, ray, args.max_events)
        if args.plot:
            from .ultrasonic_plotting import save_ultrasonic_plot
            save_ultrasonic_plot(model, ray, trace, args.plot)
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(json.dumps(trace.to_dict(), indent=2) if args.output_format == "json" else _table(trace))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
