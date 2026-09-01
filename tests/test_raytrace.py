import json
import math
from pathlib import Path

import pytest

from cylindrical_raytrace.cli import main
from cylindrical_raytrace.geometry import Ray, Vec2, ray_circle_intersections
from cylindrical_raytrace.optics import interact
from cylindrical_raytrace.tracer import CylinderModel, trace_ray
from cylindrical_raytrace.acoustics import UltrasonicModel, trace_ultrasound


def test_circle_intersections():
    assert ray_circle_intersections(Ray(Vec2(-3, 0), Vec2(1, 0)), 2) == pytest.approx([1, 5])
    assert ray_circle_intersections(Ray(Vec2(-3, 3), Vec2(1, 0)), 2) == []


def test_central_ray_does_not_bend():
    trace = trace_ray(CylinderModel(1, 2, 1, 1.33), Ray(Vec2(-3, 0), Vec2(1, 0)))
    assert len(trace.events) == 4
    assert all(event.incidence_angle_deg == pytest.approx(0) for event in trace.events)
    assert trace.termination == "exited"


def test_equal_indices_do_not_bend():
    trace = trace_ray(CylinderModel(1, 2, 1, 1), Ray(Vec2(-3, 0.5), Vec2(1, 0)))
    assert all(event.action == "refract" for event in trace.events)
    assert trace.events[0].refraction_angle_deg == pytest.approx(trace.events[0].incidence_angle_deg)


def test_snells_law_and_total_internal_reflection():
    result = interact(Vec2(math.sqrt(0.5), -math.sqrt(0.5)), Vec2(0, 1), 1, 1.5)
    assert math.sin(result.incidence_angle) == pytest.approx(1.5 * math.sin(result.refraction_angle))
    reflected = interact(Vec2(math.sqrt(0.5), -math.sqrt(0.5)), Vec2(0, 1), 1.5, 1)
    assert reflected.action == "reflect"
    assert reflected.refraction_angle is None


def test_missed_cylinder_has_no_events():
    trace = trace_ray(CylinderModel(1, 2), Ray(Vec2(-3, 3), Vec2(1, 0)))
    assert trace.events == []
    assert trace.termination == "exited"


def test_model_validation():
    with pytest.raises(ValueError):
        CylinderModel(2, 1)
    with pytest.raises(ValueError):
        CylinderModel(1, 2, n2=0)


def test_cli_json(capsys):
    status = main(["--inner-radius", "1", "--outer-radius", "2", "--n2", "1.33",
                   "--origin-x", "-3", "--origin-y", "0", "--angle-deg", "0",
                   "--output-format", "json"])
    assert status == 0
    output = json.loads(capsys.readouterr().out)
    assert len(output["events"]) == 4
    assert output["termination"] == "exited"


def test_cli_creates_plot(tmp_path: Path, capsys):
    output = tmp_path / "ray.png"
    status = main(["--inner-radius", "1", "--outer-radius", "2", "--n1", "1",
                   "--n2", "1.33", "--origin-x", "-4", "--origin-y", "0.5",
                   "--angle-deg", "0", "--plot", str(output)])
    assert status == 0
    assert output.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    capsys.readouterr()


def test_cli_reports_version(capsys):
    with pytest.raises(SystemExit) as exit_info:
        main(["--version"])
    assert exit_info.value.code == 0
    assert capsys.readouterr().out == "cylindrical-raytrace 0.2.0\n"


def test_ultrasound_crosses_layer_and_reaches_water():
    model = UltrasonicModel(4, 5)
    trace = trace_ultrasound(model, Ray(Vec2(-5.49, 0), Vec2(1, 0)))
    assert trace.events[0].from_medium == "matching"
    assert trace.events[0].to_medium == "pfa"
    assert any(event.to_medium == "water" for event in trace.events)
    assert any(event.action == "reflect" and event.to_medium is None for event in trace.events)
    assert trace.termination == "reached PZT"
    assert trace.travel_time_us > 0


def test_matching_layer_has_two_mm_arc_width():
    model = UltrasonicModel(4, 5, matching_center_angle_deg=0)
    on_edge = Vec2(5 * math.cos(0.2), 5 * math.sin(0.2))
    outside = Vec2(5 * math.cos(0.201), 5 * math.sin(0.201))
    assert model.in_matching_arc(on_edge)
    assert not model.in_matching_arc(outside)
