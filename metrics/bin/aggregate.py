"""
# Metrics aggregation command interface.

# Target executable for rendering metrics.
# Process the content of the work directory looking for other intentions that
# have had their reports trapped in.
"""
import json
from fault.system import process
from fault.system import files

from .. import calculations

# Fate records.
testforms = [
	'optimal',
	'debug',
	'coverage',
]

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
		if files and qpath.identifer[:1] == '.':
			yield root, qpath

def identify_captured_metrics(path):
	"""
	# Scan each data set for capture records.
	"""
	for dataset in path.fs_list('void')[0]:
		yield from factor_records(dataset)

def integrate_test_reports(output, forms, cache):
	testd = output/'test'
	for i in forms:
		records = cache/i
		t = testd/i
		if records.fs_type() != 'void':
			t.fs_alloc().fs_mkdir()
			test_reports = records/'.fault-test-fates'
			if test_reports.fs_type() != 'void':
				t.fs_replace(test_reports)

def integrate_syntax_profiles(path, sources, rpath=files.root):
	src = {x.rsplit('/units/', 1)[1]: json.loads((rpath@x).fs_load()) for x in sources}
	with path.fs_open('w') as f:
		json.dump(src, f)

def integrate_coverage_telemetry(output, telemetry):
	for x in identify_captured_metrics(cd/'coverage'/'telemetry'):
		pass

def main(inv:process.Invocation) -> process.Exit:
	output, cache, project, factor, *src = inv.argv # Factor Image and the Compilation Cache directory.
	od = inv.fs_pwd@output
	cd = inv.fs_pwd@cache

	# Create image directory.
	od.fs_alloc().fs_mkdir()

	integrate_syntax_profiles(od/'syntax-profiles', src, rpath=inv.fs_pwd)
	integrate_test_reports(od, testforms, cd)
	integrate_coverage_telemetry(od, cd/'coverage'/'telemetry')

	return inv.exit(0)
