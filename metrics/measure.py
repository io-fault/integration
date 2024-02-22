"""
# Measure the source presented on standard input using &syntax.profile
# and write the JSON document to standard output.

# The first record in the sequence is the aggregate profile and
# each following record describes the indentation level corresponding
# to the index. (IL-0 being the second, IL-1 being the third, etc.)
"""
import sys
from fault.system import process
from . import syntax

def main(inv:process.Invocation) -> process.Exit:
	# Ignore arguments; standard I/O processing.
	write = sys.stdout.write
	for x in syntax.profile(sys.stdin.readlines()):
		write(x)
	return inv.exit(0)
