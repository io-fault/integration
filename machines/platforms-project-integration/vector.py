"""
# Persistence methods for argument vector execution platforms.
"""
from fault.system import files
from fault.system import execution

E_NAME='F_EXECUTION'
A_RECORD='architectures'
S_RECORD='system'
P_RECORD='plans'

def fs_initialize(target:files.Path, system:str, encoding='utf-8'):
	"""
	# Create directories and files for a stored logical platform.
	"""
	(target/S_RECORD).fs_store(' '.join((system,)).encode(encoding))
	(target/P_RECORD).fs_mkdir()
	(target/A_RECORD).fs_store(b'')
	return target

def fs_update(target:files.Path, pf:execution.Platform, encoding='utf-8') -> files.Path:
	"""
	# Using the given &target filesystem path, store the platform's specification.

	# The system identifier, execution plans, and architecture priority list will be written
	# under the presumption that the leading path already exists. No checks for suitability
	# are performed.
	"""
	(target/S_RECORD).fs_store(pf.system)
	fs_update_sections(target, pf.sections(), encoding=encoding)

def fs_update_sections(target:files.Path, sections, encoding='utf-8') -> files.Path:
	"""
	# Store the given sections in the target path.
	"""
	archs = []
	plans = (target/P_RECORD)

	for aid, syns, plan in sections:
		sxp = ''.join(execution.serialize_sx_plan(plan)).encode(encoding)
		(plans/aid).fs_store(sxp)
		syns.insert(0, aid)
		archs.append(' '.join(syns))

	(target/A_RECORD).fs_store("\n".join(archs).encode(encoding))
