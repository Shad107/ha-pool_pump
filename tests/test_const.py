"""Smoke-test the const module to catch declaration-order bugs.

The v0.12.0 release shipped with `ROUTINES` declared before the
`MODE_*` constants it referenced, raising a `NameError` at import time
that took the whole integration offline. This file would have caught
that bug in CI before release.
"""
from __future__ import annotations


def test_const_imports_clean():
    """Importing `const` must not raise."""
    from custom_components.pool_pump import const  # noqa: F401


def test_routines_well_formed():
    """Each routine row has the expected shape and uses a valid mode."""
    from custom_components.pool_pump import const

    valid_modes = set(const.MODE_OPTIONS)
    assert const.ROUTINES, "ROUTINES must not be empty"
    for row in const.ROUTINES:
        key, label, icon, mode, default_min, smart_prefix, favorite = row
        assert isinstance(key, str) and key
        assert isinstance(label, str) and label
        assert isinstance(icon, str) and icon.startswith("mdi:")
        assert mode in valid_modes, f"routine {key} uses unknown mode {mode!r}"
        assert isinstance(default_min, int) and default_min > 0
        assert smart_prefix is None or isinstance(smart_prefix, str)
        assert isinstance(favorite, bool)


def test_routines_keys_unique():
    """Routine keys must be unique (used as service routine_key)."""
    from custom_components.pool_pump import const

    keys = [r[0] for r in const.ROUTINES]
    assert len(keys) == len(set(keys)), f"duplicate routine keys in {keys}"


def test_chem_params_well_formed():
    """Each chemistry parameter has the expected shape."""
    from custom_components.pool_pump import const

    for row in const.CHEM_PARAMS:
        key, label, unit, vmin, vmax, step, tgt, low, high, default_on = row
        assert vmin < vmax
        assert low <= tgt <= high
        assert low >= vmin and high <= vmax
