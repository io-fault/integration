"""
# Delineate a source file using libclang.
"""
import sys
import os
import subprocess

from fault.system import files
from fault.system import process
from fault.system import factors
from fault.system import identity
from fault.system import execution

from fault.project import root

def main(inv:process.Invocation) -> process.Exit:
	isys, iarch = identity.root_execution_context()

	args = inv.args

	# Much of this should be implemented elsewhere, and delineate is the first user.
	try:
		finder = factors.Activated
	except AttributeError:
		factors.activate()
		finder = factors.Activated

	pd = finder.find('f_intention')
	pj_id = pd.identifier_by_factor(root.types.factor@'f_intention')[0]
	pj = finder.context.project(pj_id)

	var = {
		'system': isys,
		'architecture': iarch,
		'name': 'llvm',
	}
	for fi in ['debug', 'optimal']:
		var['intention'] = fi
		fp = pj.integral(var, root.types.factor@'bin.llvm')
		if fp.fs_type() != 'void':
			break
	else:
		return inv.exit(128)

	sys.stderr.write('EXECUTABLE: ' + str(fp) + '\n')
	ki = execution.KInvocation(str(fp), [b'delineate',] + inv.args)
	pid = ki.spawn(fdmap=[(0,0), (1,1), (2,2)])
	pid, status = os.waitpid(pid, os.P_WAIT)
	delta = execution.decode_process_status(status)

	assert inv.args[-3] == '-o' # delineate ... -o output source.cx
	datadir = inv.args[-2]

	if delta.status == 0:
		# Cleanup JSON output by removing trailing commas.
		# Note that commas are expected to be \u escaped within strings.
		datadir = files.Path.from_path(inv.args[-2])

		for x in ['elements.json', 'documentation.json', 'documented.json']:
			data = datadir/x

			b = (datadir/x).fs_load()
			b = b.replace(b',}', b'}')
			b = b.replace(b',]', b']')
			(datadir/x).fs_store(b)

	return inv.exit(delta.status)

if __name__ == '__main__':
	process.control(main, process.Invocation.system())
