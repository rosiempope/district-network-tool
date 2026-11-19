from dataclasses import dataclass
from enum import Enum


class NetworkType(str, Enum):
    RADIAL = "radial"  # 3rd-gen: a tree of flow/return pipe pairs
    RING = "ring"      # ambient loop: one closed ring with spurs


class SegmentKind(str, Enum):
    BRANCH = "branch"  # pipe pair in a radial network
    RING = "ring"      # pipe on the ambient loop itself
    SPUR = "spur"      # connection from the loop out to a building


@dataclass(frozen=True)
class Segment:
    from_node: str
    to_node: str
    length_m: float
    kind: SegmentKind

    def __post_init__(self):
        if self.length_m <= 0:
            raise ValueError(
                f"Segment {self.from_node}->{self.to_node}: length_m must be > 0"
            )
        if self.from_node == self.to_node:
            raise ValueError(f"Segment {self.from_node}: starts and ends at the same node")


def _parent_map(segments, anchors):
    """Map each node to the node that feeds it. Each node may have only one."""
    parents = {}
    for s in segments:
        if s.to_node in anchors:
            raise ValueError(
                f"Pipe {s.from_node}->{s.to_node} leads into {s.to_node}, "
                "which is already part of the network core"
            )
        if s.to_node in parents:
            raise ValueError(f"Node {s.to_node} has more than one incoming pipe")
        parents[s.to_node] = s.from_node
    return parents


def _check_reaches_anchors(parents, anchors):
    """Every node must lead back to an anchor without going round in circles."""
    for node in parents:
        seen = set()
        current = node
        while current not in anchors:
            if current in seen:
                raise ValueError(f"Loop in pipes at node {node}")
            seen.add(current)
            if current not in parents:
                raise ValueError(f"Node {current} is not connected to the network")
            current = parents[current]


def _ring_nodes(ring_segments, root_node):
    """Check the ring segments form one closed loop; return the nodes on it."""
    if len(ring_segments) < 3:
        raise ValueError("A ring needs at least 3 ring segments")
    neighbours = {}
    for s in ring_segments:
        neighbours.setdefault(s.from_node, []).append(s.to_node)
        neighbours.setdefault(s.to_node, []).append(s.from_node)
    for node, linked in neighbours.items():
        if len(linked) != 2:
            raise ValueError(
                f"Ring node {node} has {len(linked)} ring pipes; every ring node needs exactly 2"
            )
    start = next(iter(neighbours))
    seen = {start}
    to_visit = [start]
    while to_visit:
        for other in neighbours[to_visit.pop()]:
            if other not in seen:
                seen.add(other)
                to_visit.append(other)
    if seen != set(neighbours):
        raise ValueError("Ring pipes form more than one separate loop")
    if root_node not in neighbours:
        raise ValueError(f"Root node {root_node} must be on the ring")
    return set(neighbours)


@dataclass(frozen=True)
class Network:
    network_type: NetworkType
    segments: tuple[Segment, ...]
    root_node: str = "plant"

    def __post_init__(self):
        if not self.segments:
            raise ValueError("A network needs at least one segment")

        allowed = {
            NetworkType.RADIAL: {SegmentKind.BRANCH},
            NetworkType.RING: {SegmentKind.RING, SegmentKind.SPUR},
        }[self.network_type]
        for s in self.segments:
            if s.kind not in allowed:
                raise ValueError(
                    f"Segment {s.from_node}->{s.to_node} is a {s.kind.value}, "
                    f"which a {self.network_type.value} network cannot have"
                )

        if self.network_type == NetworkType.RADIAL:
            anchors = {self.root_node}
            parents = _parent_map(self.segments, anchors)
            _check_reaches_anchors(parents, anchors)
        else:
            ring = [s for s in self.segments if s.kind == SegmentKind.RING]
            spurs = [s for s in self.segments if s.kind == SegmentKind.SPUR]
            anchors = _ring_nodes(ring, self.root_node)
            parents = _parent_map(spurs, anchors)
            _check_reaches_anchors(parents, anchors)

    @property
    def nodes(self) -> frozenset[str]:
        names = {self.root_node}
        for s in self.segments:
            names.update((s.from_node, s.to_node))
        return frozenset(names)

    def length_m(self, kind: SegmentKind | None = None) -> float:
        return sum(s.length_m for s in self.segments if kind is None or s.kind == kind)