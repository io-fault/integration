"""
LLVM utilities for extracting profile and coverage data.

! WARNING:
	Currently does not provide information about expansion regions.
"""
from ...probes import libllvm
from ....development.probes import libpython

__factor_type__ = 'system'
__factor_dynamics__ = 'extension'
