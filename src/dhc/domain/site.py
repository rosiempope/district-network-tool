from dataclasses import dataclass

from dhc.domain.network import Network


@dataclass(frozen=True)
class BenchmarkDemand:
    """Estimate demand from building type and floor area."""


@dataclass(frozen=True)
class AnnualDemand:
    """User supplies annual totals; an hourly shape is applied later."""

    heat_kwh_per_year: float
    cooling_kwh_per_year: float = 0.0

    def __post_init__(self):
        if self.heat_kwh_per_year < 0 or self.cooling_kwh_per_year < 0:
            raise ValueError("Annual demand cannot be negative")
        if self.heat_kwh_per_year == 0 and self.cooling_kwh_per_year == 0:
            raise ValueError("Annual demand needs a heat or cooling value above zero")


@dataclass(frozen=True)
class MeasuredDemand:
    """User supplies hourly data. Holds only the file name; an adapter reads it."""

    file_name: str

    def __post_init__(self):
        if not self.file_name.strip():
            raise ValueError("Measured demand needs a file name")


def _check_coordinates(latitude, longitude, label):
    if (latitude is None) != (longitude is None):
        raise ValueError(f"{label}: give both latitude and longitude, or neither")
    if latitude is not None:
        if not -90 <= latitude <= 90:
            raise ValueError(f"{label}: latitude must be between -90 and 90")
        if not -180 <= longitude <= 180:
            raise ValueError(f"{label}: longitude must be between -180 and 180")


@dataclass(frozen=True)
class Building:
    name: str  # also the building's node name in any network table
    building_type: str
    floor_area_m2: float
    demand: BenchmarkDemand | AnnualDemand | MeasuredDemand
    latitude: float | None = None
    longitude: float | None = None

    def __post_init__(self):
        if not self.name.strip():
            raise ValueError("Building needs a name")
        if self.floor_area_m2 <= 0:
            raise ValueError(f"Building {self.name}: floor_area_m2 must be > 0")
        _check_coordinates(self.latitude, self.longitude, f"Building {self.name}")


@dataclass(frozen=True)
class Site:
    name: str
    buildings: tuple[Building, ...]
    plant_latitude: float | None = None
    plant_longitude: float | None = None

    def __post_init__(self):
        if not self.buildings:
            raise ValueError("A site needs at least one building")
        names = [b.name for b in self.buildings]
        if len(names) != len(set(names)):
            raise ValueError("Building names must be unique")
        _check_coordinates(self.plant_latitude, self.plant_longitude, "Plant")

    @property
    def total_floor_area_m2(self) -> float:
        return sum(b.floor_area_m2 for b in self.buildings)

    def check_network(self, network: Network) -> None:
        """Raise if this network does not suit this site's buildings."""
        building_names = {b.name for b in self.buildings}
        if network.root_node in building_names:
            raise ValueError(f"A building cannot be named {network.root_node}: that is the plant node")
        missing = sorted(building_names - network.nodes)
        if missing:
            raise ValueError(f"Buildings not found in the network: {', '.join(missing)}")