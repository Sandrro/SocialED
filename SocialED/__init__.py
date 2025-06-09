# -*- coding: utf-8 -*-


from . import dataset
from . import metrics
from . import utils
from . import detector

# The tests module pulls in heavy dependencies and is not required for normal
# package usage. Import it lazily so missing optional dependencies do not break
# basic functionality such as loading datasets.
try:  # pragma: no cover - optional import
    from . import tests
except Exception as exc:  # pragma: no cover - graceful fallback
    import warnings
    warnings.warn(
        f"Tests module could not be imported: {exc}",
        ImportWarning,
    )
    tests = None

__all__ = ['dataset', 'metrics', 'utils', 'detector', 'tests']
