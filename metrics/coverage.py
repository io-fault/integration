"""
# Counter placement tooling for identifying the parent element.
"""
import contextlib
import json
from itertools import islice, repeat
from collections import Counter, defaultdict

from fault.range.types import Mapping
from fault.syntax.types import Area, Address

# "{record-count} {source-file-path}\n"
def _parse_map_sources(lines):
	i = 0
	for line in lines:
		rcount, src = line.split(maxsplit=1)
		yield i, int(rcount), src
		i += 1

# "{metrics-isolation} {record-count} {source-file-path}\n"
def _parse_sources(lines):
	i = 0
	for line in lines:
		isolation, rcount, src = line.split(maxsplit=2)
		yield isolation, i, int(rcount), src
		i += 1

def _parse_areas(lines):
	for line in lines:
		yield tuple(map(int, line.split(maxsplit=4)))
		#startl, startc, stopl, stopc = map(int, line.split(maxsplit=4))
		#yield Area((Address((startl, startc)), Address((stopl, stopc))))

def index_regions(regions):
	"""
	# Construct an index from source regions for use with &integrate_lcounters.

	# [ Parameters ]
	# /regions/
		# A mapping of source file identifiers, paths, associated
		# with a list of syntax areas.

	# [ Returns ]
	# An index for converting L-counters to fault syntax counters.
	"""

	idx = {}
	for src, areas in regions.items():
		for a in areas:
			ln, co, eln, eco = map(int, a)
			idx[(src, ln, co)] = f"{ln} {co} {eln} {eco}\n"

	return idx

def integrate_lcounters(index, fsc, lcounters):
	"""
	# Convert the counters in &lcounters into fault syntax counters, &fsc, using
	# the given &index to identify the full region.
	"""

	isolation = None
	srcfile = None
	counters = 0

	with contextlib.ExitStack() as stack:
		src = stack.enter_context((fsc/'sources').fs_open('a'))
		counts = stack.enter_context((fsc/'counts').fs_open('a'))
		areas = stack.enter_context((fsc/'areas').fs_open('a'))

		for line in lcounters:
			if line[:1] == '@':
				# Change file.
				if isolation and srcfile and counters:
					src.write(f"{isolation} {counters} {srcfile}\n")
				srcfile = line[1:].strip()
			elif line[:1] == '&':
				# Change isolation
				if isolation and srcfile and counters:
					src.write(f"{isolation} {counters} {srcfile}\n")
				isolation = line[1:].strip()
			else:
				ln, co, count = map(int, line.split())
				try:
					sa = index[(srcfile, ln, co)]
				except KeyError:
					continue

				counters += 1
				areas.write(sa)
				counts.write(str(count) + '\n')
				continue

			# Increments reset when isolation or file is changed.
			counters = 0

		if isolation and srcfile and counters:
			src.write(f"{isolation} {counters} {srcfile}\n")

def factor_records(root):
	"""
	# Scan the tree for data files and select the segment
	# from &root that can be used to identify the origin of
	# the record.

	# Yields the path and segment identifying the data record.
	"""

	# Essentially, scan for directories containing regular files.
	for d, files in root.fs_index():
		qpath = d.segment(root)
		if files and qpath.identifier[:1] == '.':
			yield root, qpath

def identify_source_areas(path):
	"""
	# Scan the directory for nodes containing regular files.
	"""

	for subdir in path.fs_iterfiles('directory'):
		for d, df in subdir.fs_index():
			if df:
				yield d

def identify_captured_metrics(path):
	"""
	# Scan each data set for capture records.
	"""

	for dataset in path.fs_list('void')[0]:
		yield from factor_records(dataset)

def join_fault_syntax_areas(sources, areas, types, *, Type=dict):
	ra = {}
	rt = {}

	for lineno, rcount, src in sources:
		ra[src] = list(islice(areas, 0, rcount))
		rt[src] = ''.join(islice(types, 0, rcount))

	return ra, rt

def load_fault_syntax_areas(sources, areas, types):
	"""
	# Load the areas from the triple of &sources,
	# &areas, and &types.

	# Used to read source counter maps.
	"""

	with contextlib.ExitStack() as xs:
		src = xs.enter_context(sources.fs_open('r'))
		sas = xs.enter_context(areas.fs_open('r'))

		if types.fs_type() == 'data':
			typ = xs.enter_context(types.fs_open('r'))
			typiter = typ.read() # Sequence of type code characters.
		else:
			typ = None
			typiter = repeat('+')

		srciter = _parse_map_sources(map(str.strip, src.readlines()))
		aiter = _parse_areas(map(str.strip, sas.readlines()))

		return join_fault_syntax_areas(srciter, aiter, typiter)

def join_fault_syntax_counters(sources, areas, counts, *, Type=Counter):
	counters = defaultdict(Type)

	for isolation, lineno, rcount, src in sources:
		c = counters[src]
		for k, d in zip(islice(areas, 0, rcount), islice(counts, 0, rcount)):
			c[k] += d

	return counters

def load_fault_syntax_counters(sources, areas, counts):
	"""
	# Load the counters from the triple of &sources,
	# &areas, and &counts.

	# Used to read source coverage counters.
	"""

	with contextlib.ExitStack() as xs:
		src = xs.enter_context(sources.fs_open('r'))
		sas = xs.enter_context(areas.fs_open('r'))
		cnt = xs.enter_context(counts.fs_open('r'))

		srciter = _parse_sources(map(str.strip, src.readlines()))
		aiter = _parse_areas(map(str.strip, sas.readlines()))
		citer = (int(x.strip()) for x in cnt)

		return join_fault_syntax_counters(srciter, aiter, citer)

def structure_area(vector):
	return Area((
		Address(vector[:2]),
		Address(vector[2:]),
	))

def load_metrics_aggregates(path):
	"""
	# Read areas and constituents files from the given metrics image directory.
	"""

	abounds = (path/'coverage-areas')
	atypes = (path/'area-types')
	acounts = (path/'constituents')

	with abounds.fs_open('r') as f:
		areas = json.load(f)
		for k in areas:
			areas[k] = list(map(structure_area, areas[k]))

	# Load and restructure the covered areas as an Area of Address pairs.
	with acounts.fs_open('r') as f:
		gcounts = json.load(f)
		for fn in gcounts:
			counts = gcounts[fn]
			for k in counts:
				counts[k][0] = list(map(structure_area, counts[k][0]))

	with atypes.fs_open('r') as f:
		types = json.load(f)

	return areas, gcounts, types

def descend(mapping, current, elements):
	for er in elements:
		typ, sub, d = er
		if 'area' not in d:
			# Nothing to index.
			continue

		eid = d.get('identifier') or None
		if eid is None:
			# Not identified.
			continue

		if typ == 'parameter':
			# Parameters have areas and identities, but it is not
			# desired to associate coverage with them even if a language
			# can associate expressions. Prefer to keep it with the function.
			continue

		area = Area(map(Address, d['area']))
		path = current + (eid,)
		mapping[area] = path

		if len(sub) > 0:
			descend(mapping, path, sub)

def index_elements(dsrc):
	"""
	# Create a range mapping from the given delineated source, &dsrc.
	# The keys are associated with the element path of the syntax
	# areas holding the content of the element.
	"""

	typ, elements, d = dsrc
	sam = Mapping(default=Area((Address((0, 0)), Address((0, 0)))))
	if 'area' not in d:
		return sam
	area = Area(map(Address, d['area']))

	descend(sam, (), elements)
	sam[area] = tuple()
	return sam

def total(index, areas, types, counts):
	"""
	# Create totals for the profile.
	"""

	# Cache the mapping index.
	zeros = set(index)
	total = Counter()

	for origin, coverage in counts.items():
		careas, ccounts, cexpansions = coverage
		zeros.difference_update(careas)
		for a, c in zip(careas, ccounts):
			total[a] += c

	return list(zeros), dict(total)

def organize_counters(index, areas, types, counts):
	"""
	# Organize the integrated coverage metrics for reporting and reveal analysis.
	"""

	# Cache the mapping index.
	for origin, coverage in counts.items():
		careas, ccounts, cexpansions = coverage
		zeros.difference_update(careas) # Only non-zero.
		for a, c in zip(careas, ccounts):
			total[a] += c

	return ncounters, zeros, dict(total)

def element_area_index(index):
	"""
	# Convert an area-to-element index into a serializable form.
	"""

	asets = defaultdict(list)
	for k, v in index.items():
		asets['.'.join(v)].append(tuple(k[0]) + tuple(k[1]))

	for v in asets.values():
		v.sort()

	return asets

def factor_source_profile(elements, areas, types, counts):
	"""
	# Build a serializable representation of the given coverage data.
	"""

	# Group coverage data by element.
	rmap = index_elements(elements)
	index = {x: rmap.get(x, ()) for x in areas}

	# Calculate per-element counter index.
	zeros, totals = total(index, areas, types, counts)

	return {
		'elements': element_area_index(index),
		'zeros': sorted([tuple(x[0]) + tuple(x[1]) for x in zeros]),
		'coverage': [tuple(x[0]) + tuple(x[1]) for x in totals],
		'counts': [v for v in totals.values()],
	}

def annotation(zeros, elements):
	"""
	# Identify the missed areas in elements for annotation reporting.
	"""

	# Total area count and exact missing areas.
	# Loaded during representation rendering, it's desired to be able
	# to identify the per-element missed areas
	missed = [m for m in elements if m in zeros]
	return (len(elements), len(missed), missed)
