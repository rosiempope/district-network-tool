from dataclasses import dataclass


@dataclass(frozen=True)
class Segment:
    from_node: str
    to_node: str
    length_m: float

    def __post_init__(self):
        if self.length_m <= 0:
            raise ValueError(
                f"Segment {self.from_node}->{self.to_node}: length_m must be > 0"
            )

@dataclass(frozen=True)
class Building:
    name: str
    building_type: str
    floor_area_m2: float
    node: str  # the network node this building connects to