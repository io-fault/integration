"""
# Construction Context resolution support.
"""
import os
from collections.abc import Iterator

from fault.system import files
from ..root import query

def select(
		local:object,
		product:files.Path=None,
		environment:str='SYSTEMCONTEXT',
	) -> tuple[str, files.Path]:
	"""
	# Generate the possible locations of construction contexts.
	# Usually, the first existing path should be used.

	# Some entries will only be present when a required environment variable
	# is present and not an empty string. Existence must be checked by caller:

	#!syntax/python
		[x for x in context.select(...) if x[1].fs_type() == 'directory']

	# The first element of the tuples is a string describing the origin of the path.
	"""

	if local is not None:
		# A, normally, user provided path.
		yield ('local', files.Path.from_path(local))

	if os.environ.get(environment, None):
		yield ('environment', files.Path.from_absolute(os.environ[environment]))

	if product is not None:
		yield ('product', product/'.system')

	yield ('fault', query.system())

def resolve(override:str=None, product=None) -> tuple[str, files.Path]:
	"""
	# Use &select to find the highest priority construction context whose directory
	# exists on the filesystem. The identified path is not verified to conform
	# to a protocol so subsequent checks may be required.
	"""

	for pair in select(local=override, product=product):
		if pair[1].fs_type() == 'directory':
			return pair
	else:
		return ('unavailable', None)
