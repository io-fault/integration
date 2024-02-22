"""
# Metrics aggregation command interface.

# Target executable for rendering metrics.
# Process the content of the work directory in conjunction with telemetry data.
"""
import json
from fault.system import process
from fault.system import files

from . import calculations

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

def identify_captured_metrics(path):
	"""
	# Scan each data set for capture records.
	"""

	for dataset in path.fs_list('void')[0]:
		yield from factor_records(dataset)

def integrate_test_reports(output, cache, telemetry):
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

	testd.fs_replace(records/'.fault-test-fates')

def integrate_syntax_profiles(path, sources, rpath=files.root):
	src = {x.rsplit('/units/', 1)[1]: json.loads((rpath@x).fs_load()) for x in sources}
	with path.fs_open('w') as f:
		json.dump(src, f)

def integrate_coverage_telemetry(output, telemetry):
	for x in identify_captured_metrics(telemetry):
		pass

def main(inv:process.Invocation) -> process.Exit:
	output, cache, telemetry, project, factor, *src = inv.argv # Factor Image and the Compilation Cache directory.
	od = inv.fs_pwd@output
	cd = inv.fs_pwd@cache
	td = inv.fs_pwd@telemetry

	# Create image directory.
	od.fs_alloc().fs_mkdir()

	integrate_syntax_profiles(od/'syntax-profiles', src, rpath=inv.fs_pwd)
	integrate_test_reports(od, cd, td)
	integrate_coverage_telemetry(od, td/'coverage')

	return inv.exit(0)
