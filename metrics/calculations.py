"""
# Calculations for project metrics.
"""
from collections.abc import Iterable, Sequence

import collections
import functools
import itertools
import operator

from . import types

def edges(view:int, vector:Sequence):
	"""
	# Get the minimums and maximums of the sorted &vector.
	# Where &view
	"""
	if len(vector) > (view * 2):
		v = []
		v.extend(vector[0:view])
		v.extend(vector[-view:])
	else:
		v = list(vector)
	return v

def deltas(values:Iterable, reference, exponent=2):
	"""
	# Calculate running totals for measuring distance and variance relative to &reference.

	# Primarily used by &statistics to construct a &types.Statistics instance.
	"""
	deltas = 0
	areas = 0

	for m, c in values:
		d = m - reference
		deltas += abs(d) * c
		areas += (d ** exponent) * c

	return deltas, areas

def statistics(source:Iterable,
		view:int=8, scale=1, exponent=2, *,
		attributes=tuple(
			map(operator.attrgetter, ['subject', 'total', 'count'])
		),
		Counter=collections.Counter,
		Product=types.Product.from_factors,
		Partial=functools.partial,
		sum=sum, map=map, sorted=sorted,
	) -> types.Statistics:
	"""
	# Construct a &types.Statistics instance from the given iterable of numbers.

	# [ Parameters ]
	# /source/
		# An iterator of values to calculate statistics from.
	# /view/
		# The size of the edges stored by the profiles.
	# /scale/
		# The magnification to use when counting values.
	# /exponent/
		# The exponent to use when calculating the variance.
	"""
	# Scale the values down and count them.
	View = Partial(edges, view)
	cs = Counter()
	cs.update((m // scale) for m in source)

	# Scale the value back up and create the product vector representing the data set.
	vector = [Product((v * scale), c) for v, c in cs.items()]

	# Build &types.Profile instances for the &types.Statistics instance.
	s, m, f = [
		types.Profile(sum(map(ag, vector)), View(sorted(vector, key=ag)))
		for ag in attributes
	]

	# Get average-value for calculating deviation and distance.
	avg = m.total / f.total
	dev = deltas(((x.subject, x.count) for x in vector), avg, exponent=exponent)

	return types.Statistics(len(vector), *dev, s, m, f)

def collapse(data, merge, dimensions:int=1) -> dict:
	"""
	# Collapse dimensions in the given &data by removing
	# the specified number of &dimensions from the key and merging
	# data with the given &merge function.

	# Collapse is primarily used by &aggregates.

	# [ Parameters ]
	# /data/
		# A &collections.defaultdict instance designating the data to collapse.
	# /merge/
		# A callable that can combine measurements. For &collections.Counter,
		# this is &collections.Counter.update. For &list, this is &list.extend.
	"""
	collapsed = collections.defaultdict(data.default_factory)
	collapse_key = functools.lru_cache(128)(lambda x: x[:-dimensions])

	for k, v in data.items():
		merge(collapsed[collapse_key(k)], v)

	return collapsed

def aggregate(durations, islice=itertools.islice):
	"""
	# Aggregate profile data using the &statistics function.
	# &data is expected to be a sequence of positive numbers
	# where the even indexes (and zero) are cumulative, and the odds are
	# resident.
	"""
	ctimes = statistics(islice(data, 0, None, 2))
	rtimes = statistics(islice(data, 1, None, 2))
	return (ctimes, rtimes)

def timings(data):
	context = collapse(data, list.extend)
	times_groups = {
		('floor', 'call', 'outercall', 'test'): data,
		('context', 'call', 'outercall'): context,
	}

	times_groups[('ceiling', 'call')] = collapse(context, list.extend)
	return times_groups
