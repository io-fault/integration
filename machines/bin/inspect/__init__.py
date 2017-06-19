"""
# libclang tool for extracting XML used to delineate sources.

# The emitted output uses an anonymous schema and should not be relied on
# directly. The &.bin.delineate executable is provided for consistent output.

# [ Engineering ]
# The tool does not descend into functions and expressions leaving this to be
# used strictly for delineation.
"""
from ...probes import libclang
__factor_domain__ = 'system'
__factor_type__ = 'executable'
