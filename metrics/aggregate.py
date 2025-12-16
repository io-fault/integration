"""
# Metrics aggregation command interface.

# Target executable for rendering metrics.
# Process the content of the work directory in conjunction with telemetry data.
"""
import operator
import json
import collections
from fault.system import process
from fault.system import files

from . import calculations
from . import coverage

first = operator.itemgetter(0)

def integrate_test_reports(output, cache, telemetry, delineated):
	records = telemetry/'test'

	if records.fs_type() == 'void':
		# Not a test; no report emitted to identified metrics directory.
		return

	assert output.fs_type() != 'void'
	testd = output/'test'
	try:
		testd.fs_mkdir()
	except FileExistsError:
		pass

	testd.fs_replace(records/'.fault-test-reports')

def integrate_syntax_profiles(path, sources, rpath=files.root):
	src = {x.rsplit('/units/', 1)[1]: json.loads((rpath@x).fs_load()) for x in sources}
	with path.fs_open('w') as f:
		json.dump(src, f)

def regroup_coverage(consolidated):
	"""
	# Given consolidated coverage data, regroup the key so
	# that all producers (tests) are under a single path key.
	"""

	rg = collections.defaultdict(dict)
	for k, v in consolidated.items():
		if k[0] not in rg:
			rg[k[0]] = {}
		rg[k[0]]['/'.join(k[1:])] = v
	return rg

def structure_coverage(consolidated):
	"""
	# Structure regrouped, consolidated coverage for JSON serialization.
	"""

	fc = {}
	for filepath, data in consolidated.items():
		r = fc[filepath] = {}

		for producer, counters in data.items():
			ordered = list(counters.items())
			ordered.sort(key=first)
			areas = [x[0] for x in ordered]
			counts = [x[1] for x in ordered]

			# [syntax-area, non-zero-counts, expansion-paths]
			r[producer] = [areas, counts, {}]
	return fc

def integrate_coverage_maps(output, cache, telemetry, delineated, pfp, sfp):
	maps = delineated
	if maps.fs_type() != 'directory':
		# No coverage data.
		return

	areas = {}
	types = {}
	for rsrc in coverage.identify_source_areas(maps):
		a, t = coverage.load_fault_syntax_areas(rsrc/'sources', rsrc/'areas', rsrc/'types')
		areas.update(a)
		types.update(t)

	with (output/'coverage-areas').fs_open('w') as f:
		json.dump(areas, f)
	with (output/'area-types').fs_open('w') as f:
		json.dump(types, f)

	return areas

def integrate_coverage_capture(regions, output, cache, telemetry, delineated, pfp, sfp):
	ct = telemetry / 'coverage'
	if ct.fs_type() != 'directory':
		# No coverage data.
		return

	# Usually, there is one process (pid) per test.
	# However, tests may execute subprocesses,
	# so consolidation across PIDs is necessary.
	consolidated = collections.defaultdict(collections.Counter)
	for x in coverage.identify_captured_metrics(ct):
		leading, segment = x

		if segment.identifier != '.fault-syntax-counters':
			# Only format currently supported.
			continue

		producer = tuple(segment.container)
		fsc = leading // segment

		# Split l-counters into standard form using an index built from regions.
		lcounters = (fsc/'l-counters')
		if lcounters.fs_type() == 'data':
			idx = coverage.index_regions(regions or {})
			with lcounters.fs_open('r') as dc:
				coverage.integrate_lcounters(idx, fsc, dc.readlines())

		try:
			data = coverage.load_fault_syntax_counters(fsc/'sources', fsc/'areas', fsc/'counts')
		except FileNotFoundError:
			# Need all three files to contribute coverage data.
			pass
		else:
			for filepath, counters in data.items():
				cid = (filepath,) + producer
				consolidated[cid].update(counters)

	# Per-test data.
	consolidated = regroup_coverage(consolidated)
	with (output/'constituents').fs_open('w') as f:
		json.dump(structure_coverage(consolidated), f)

def main(inv:process.Invocation) -> process.Exit:
	output, cache, telemetry, dimage, project, factor, *src = inv.argv # Factor Image and the Compilation Cache directory.
	od = inv.fs_pwd@output
	cd = inv.fs_pwd@cache
	td = inv.fs_pwd@telemetry
	dd = inv.fs_pwd@dimage

	# Create image directory.
	od.fs_alloc().fs_mkdir()

	integrate_syntax_profiles(od/'syntax-profiles', src, rpath=inv.fs_pwd)
	integrate_test_reports(od, cd, td, dd)
	regions = integrate_coverage_maps(od, cd, td, dd, project, factor)
	integrate_coverage_capture(regions, od, cd, td, dd, project, factor)

	return inv.exit(0)
