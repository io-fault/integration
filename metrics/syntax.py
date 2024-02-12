"""
# Calculate syntax line statistics using the &profile function.
"""
import json
import collections
from collections.abc import Iterable
from .calculations import statistics

def line_metrics(line:str) -> (int, int):
	"""
	# Identify the indentation level and the number of visible characters.
	"""
	il = -1
	for i, c in enumerate(line):
		if c != '\t':
			il = i
			break
	else:
		# Disregard whitespace only.
		il = 0

	nvc = sum(map(len, line.split()))
	return (il, nvc)

def profile(source:Iterable[str]) -> Iterable[str]:
	"""
	# Emit a statistics profile using &line_metrics
	# against the given &source lines.

	# The yieled values intend to form a JSON document.
	"""

	# Collect the size of the lines with respect to
	# the indentation level.
	groupings = collections.defaultdict(list)
	all_values = []
	for il, c in map(line_metrics, source):
		groupings[il].append(c)
		all_values.append(c)

	# Force single entries to avoid divide by zero errors.
	if all_values:
		# Presuming JSON compatible repr.
		yield '[\n\t'
		yield json.dumps(statistics(all_values).summary())
		for il, values in groupings.items():
			yield ',\n\t'
			yield json.dumps(statistics(values).summary())
		yield '\n]\n'
	else:
		# Empty file.
		yield '[]\n'
