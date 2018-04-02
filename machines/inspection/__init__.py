"""
# libclang tool for extracting XML used to delineate sources.

# The emitted output uses an anonymous schema and should not be relied on
# directly. The &.bin.delineate executable is provided for consistent output.

# [ Engineering ]
# The tool does not descend into functions and expressions leaving this to be
# used strictly for delineation.
"""
__factor_domain__ = 'source'
__factor_type__ = 'library'

type = 'system/executable[llvm/libclang]'
