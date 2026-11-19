import pytest
from dhc.domain.network import Network, NetworkType, Segment, SegmentKind
from dhc.domain.site import AnnualDemand, BenchmarkDemand, Building, MeasuredDemand, Site


def building(name="A", **kwargs):
    defaults = dict(building_type="office", floor_area_m2=1000.0, demand=BenchmarkDemand())
    defaults.update(kwargs)
    return Building(name=name, **defaults)


def small_network():
    segments = (
        Segment("plant", "A", 100, SegmentKind.BRANCH),
        Segment("A", "B", 50, SegmentKind.BRANCH),
    )
    return Network(NetworkType.RADIAL, segments)


def test_valid_site():
    site = Site("Test", (building("A"), building("B")))
    assert site.total_floor_area_m2 == 2000


def test_site_needs_a_building():
    with pytest.raises(ValueError):
        Site("Empty", ())


def test_rejects_duplicate_building_names():
    with pytest.raises(ValueError):
        Site("Dupes", (building("A"), building("A")))


def test_rejects_zero_floor_area():
    with pytest.raises(ValueError):
        building(floor_area_m2=0)


def test_rejects_latitude_without_longitude():
    with pytest.raises(ValueError):
        building(latitude=51.5)


def test_rejects_out_of_range_latitude():
    with pytest.raises(ValueError):
        building(latitude=95, longitude=0)


def test_accepts_coordinates():
    building(latitude=51.5, longitude=-0.3)


def test_annual_demand_rejects_negative():
    with pytest.raises(ValueError):
        AnnualDemand(heat_kwh_per_year=-1)


def test_annual_demand_rejects_all_zero():
    with pytest.raises(ValueError):
        AnnualDemand(heat_kwh_per_year=0, cooling_kwh_per_year=0)


def test_measured_demand_needs_file_name():
    with pytest.raises(ValueError):
        MeasuredDemand(file_name=" ")


def test_network_must_contain_every_building():
    site = Site("Test", (building("A"), building("C")))
    with pytest.raises(ValueError):
        site.check_network(small_network())


def test_network_accepts_buildings_at_any_node():
    site = Site("Test", (building("A"), building("B")))  # A is an intermediate node
    site.check_network(small_network())


def test_building_cannot_be_named_like_the_plant():
    site = Site("Test", (building("plant"),))
    with pytest.raises(ValueError):
        site.check_network(small_network())