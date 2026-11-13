import pytest
from dhc.domain.config import Segment


def test_segment_rejects_zero_length():
    with pytest.raises(ValueError):
        Segment("plant", "n1", 0)