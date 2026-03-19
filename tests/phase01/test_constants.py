"""
Phase 1 — DATA-06 unit test.
Verifies: PRODUCT_IDS constant is defined in constants.py.
No Docker container required — pure unit test.
"""
import sys
import os
import pytest

# Ensure seeds/ directory is on path so we can import constants.py
_seeds_dir = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "db", "seeds")
)
if _seeds_dir not in sys.path:
    sys.path.insert(0, _seeds_dir)


def test_product_ids_defined():
    """DATA-06: PRODUCT_IDS is importable and contains exactly IDs 101-110."""
    try:
        from constants import PRODUCT_IDS
    except ImportError:
        pytest.fail(
            "Could not import PRODUCT_IDS from constants.py. "
            "Create multi-db-sql-agent/db/seeds/constants.py with PRODUCT_IDS = [101..110]"
        )

    assert isinstance(PRODUCT_IDS, list), f"PRODUCT_IDS must be a list, got {type(PRODUCT_IDS)}"
    assert len(PRODUCT_IDS) == 10, f"PRODUCT_IDS must have 10 entries, got {len(PRODUCT_IDS)}"
    assert set(PRODUCT_IDS) == set(range(101, 111)), (
        f"PRODUCT_IDS must contain exactly {{101, 102, ..., 110}}, got {sorted(PRODUCT_IDS)}"
    )


def test_product_ids_are_integers():
    """DATA-06: All PRODUCT_IDS values are integers."""
    try:
        from constants import PRODUCT_IDS
    except ImportError:
        pytest.fail("constants.py not found")

    for pid in PRODUCT_IDS:
        assert isinstance(pid, int), f"Expected int, got {type(pid)} for value {pid}"
