import json
import math

import pytest

from cylindrical_raytrace.cli import main
from cylindrical_raytrace.geometry import Ray, Vec2, ray_circle_intersections
from cylindrical_raytrace.optics import interact
from cylindrical_raytrace.tracer import CylinderModel, trace_ray


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
