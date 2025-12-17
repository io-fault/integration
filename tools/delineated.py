"""
# Copy and correct delineated json files to be free of trailing commas.

# The clang delineation tool intentionally leaves trailing commas in order
# to simplify serialization procedures. However, JSON mandates their absence.

# In order for this tool to operate safely, commas present in JSON strings must be escaped.
"""

import os
from fault.system import files
from fault.system import process
from fault.system import execution
from ..metrics import coverage

def main(inv:process.Invocation) -> process.Exit:
	cc, executable, target, root = map(files.Path.from_path, inv.argv)

	# System Path map. Built from system-path files.
	spm = {}

	# Each delineated source file is a directory of JSON and coverage maps.
	for d, ds in root.fs_index():
		di = {x.identifier: x for x in ds}
		if 'elements.json' not in di:
			# Not a unit of interest without elements.json.
			continue

		# Create the source's directory in the delineated image.
		urpath = d.segment(root)
		(target + urpath).fs_alloc().fs_mkdir()

		# Build (source) system path to delineated image source directory.
		# Used to simplify splitting the regions file if any.
		syspath = di['system-path'].fs_load()
		spm[syspath.decode('utf-8')] = (target + urpath)

		for k in ['system-path', 'areas', 'sources']:
			if k in di:
				f = di.pop(k)
				(target + f.segment(root)).fs_store(f.fs_load())

		# Correct trailing commas left by source delineation.
		for f in di.values():
			rpath = f.segment(root)
			b = f.fs_load()
			b = b.replace(b',}', b'}')
			b = b.replace(b',]', b']')
			(target + rpath).fs_store(b)

	# Iterate over the coverage tools and extract the coverage region data.
	fd = os.open(target/'.regions', os.O_WRONLY|os.O_CREAT)
	for mapper in (cc/'.coverage-tools').fs_iterfiles():
		exepath = str(mapper)
		ki = execution.KInvocation(exepath, [exepath, "regions", str(executable)])
		pid = ki.spawn(fdmap=[(0, 0), (fd, 1), (2, 2)])

		# Block to avoid concurrent writesi to .regions.
		status = os.waitpid(pid, 0)
	os.close(fd)

	# Split region data into areas and sources.
	areas = {fp: set() for fp in spm}
	with open(target/'.regions', 'r') as f:
		areas = coverage.organize_ipquery_syntax_areas(spm, f.readlines())

	# Write areas and sources for all the source files.
	coverage.sequence_syntax_areas(spm, areas)

	return inv.exit(0)

if __name__ == '__main__':
	process.control(main, process.Invocation.system())
