"""Unit tests for weighted sampling strategy helpers."""

import random
from types import SimpleNamespace

from app.api.v1.inspection_sampling import (
    _normalize_weight,
    _weighted_sample_without_replacement,
)


def test_normalize_weight_keeps_minimum_positive() -> None:
    assert _normalize_weight(None) == 1.0
    assert _normalize_weight(-5) == 1.0
    assert _normalize_weight(0) == 1.0
    assert _normalize_weight(3) == 4.0


def test_weighted_sampling_without_replacement_no_duplicates() -> None:
    candidates = [
        SimpleNamespace(id=1, active_repair_weight=0),
        SimpleNamespace(id=2, active_repair_weight=3),
        SimpleNamespace(id=3, active_repair_weight=9),
    ]

    random.seed(20260411)
    picked = _weighted_sample_without_replacement(candidates, 5)

    assert len(picked) == 3
    assert len({room.id for room in picked}) == 3


def test_weighted_sampling_prefers_higher_weight_in_aggregate() -> None:
    high = SimpleNamespace(id=1, active_repair_weight=80)
    low = SimpleNamespace(id=2, active_repair_weight=1)

    random.seed(42)
    high_hit = 0
    low_hit = 0
    for _ in range(500):
        picked = _weighted_sample_without_replacement([high, low], 1)
        assert len(picked) == 1
        if picked[0].id == high.id:
            high_hit += 1
        else:
            low_hit += 1

    assert high_hit > low_hit
    assert high_hit >= 420
