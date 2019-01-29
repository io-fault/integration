"""
# Incorporate the constructed factors for use by the system targeted by the Construction Context.

# This copies constructed files into a filesystem location that Python requires them
# to be in order for them to be used. For fabricated targets, this means placing
# bytecode compiles into (system/filename)`__pycache__` directories. For Python extension
# modules managed with composite factors, this means copying the constructed extension
# library into the appropriate package directory.
"""
import os
import sys

from fault.project import library as libproject
from fault.project import explicit

from fault.system import process
from fault.system import python
from fault.system import files
from fault.system import identity

try:
	import importlib.util
	cache_from_source = importlib.util.cache_from_source
except (ImportError, AttributeError):
	try:
		import imp
		cache_from_source = imp.cache_from_source
		del imp
	except (ImportError, AttributeError):
		# Make a guess preferring the cache directory.
		try:
			import os.path
			def cache_from_source(filepath):
				return os.path.join(
					os.path.dirname(filepath),
					'__pycache__',
					os.path.basename(filepath) + 'c'
				)
		except:
			raise
finally:
	pass

def main(inv:process.Invocation) -> process.Exit:
	"""
	# Incorporate the constructed targets.
	"""
	role, *factors = inv.args
	env = os.environ
	role = None

	py_variants = dict(zip(['system', 'architecture'], identity.python_execution_context()))
	os_variants = dict(zip(['system', 'architecture'], identity.root_execution_context()))

	for x in map(files.Path.from_path, factors):
		context = x.identifier

		wholes, composites = explicit.query(x)

		# Handle bytecode caches.
		for fpath, data in wholes.items():
			sources = data[-1]
			if not sources:
				continue

			cache_dir = sources[0] * '__pycache__'
			if not cache_dir.exists():
				cache_dir.init('directory')

			caches = map(files.Path.from_absolute, map(cache_from_source, map(str, sources)))
			prefix = x.extend(fpath)

			for src, cache in zip(sources, caches):
				name, *ext = src.identifier.split('.')
				var = {'name': name}
				var.update(py_variants)
				segment = libproject.compose_integral_path(var)

				i = (prefix * '__f-int__').extend(segment)
				if role is not None:
					i = i.suffix('.%s.i' %(role,))
				else:
					i = i.suffix('.i')

				sys.stdout.write("[&. %s -> %s]\n" %(i, cache))
				cache.link(i, relative=True)

		for fpath, data in composites.items():
			if 'extensions' not in fpath:
				continue
			domain, typ, syms, sources = data

			fpath = list(fpath)
			prefix = x.extend(fpath) * '__f-int__'

			var = {'name': fpath[-1]}
			var.update(os_variants)
			segment = libproject.compose_integral_path(var)

			i = prefix.extend(segment)
			if role is not None:
				i = i.suffix('.%s.i' %(role,))
			else:
				i = i.suffix('.i')

			del fpath[fpath.index('extensions')]
			target = x.extend(fpath)
			export = target.suffix('.so')

			# Make sure the parent exists.
			if not target.container.exists():
				target.container.init('directory')

			sys.stdout.write("[&. %s -> %s]\n" %(i, export))
			export.link(i, relative=True)

	return inv.exit(0)

if __name__ == '__main__':
	process.control(main, process.Invocation.system())
