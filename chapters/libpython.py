"""
# Developer APIs extracting the documentation and structure of Python objects.
"""

import sys
import os
import os.path
import inspect
import functools
import itertools
import hashlib
import types
import lzma
import codecs
import contextlib
import importlib
import typing
import pickle

from ..system import libfactor
from ..routes import library as libroutes
from ..xml import library as libxml
from ..xml import libpython as libxmlpython
from ..text import library as libtext

from ..development import libxml as devxml

serialization = libxmlpython.Serialization() # currently only utf-8 is used.

namespaces = {
	'f': 'http://fault.io/xml/factor',
}

# If pkg_resources is available, use it to identify explicit namespace packages.
try:
	import pkg_resources
	def is_namespace(path):
		return path in pkg_resources._namespace_packages

	def pkg_distribution(loader):
		return pkg_resources.Distribution.from_filename(loader.archive)
except ImportError:
	# no namespace concept without pkg_resources
	def is_namespace(path):
		return False

	def pkg_distribution(loader):
		return None

class Query(object):
	"""
	# Query set for inspecting objects for documentation generation.
	"""

	class_ignore = {
		'__doc__',     # Extracted explicitly.
		'__weakref__', # Runtime specific information.
		'__dict__',    # Class content.
		'__module__',  # Supplied by context.

		# Exception subclasses will have these attributes.
		'__cause__',
		'__context__',
		'__suppress_context__',
		'__traceback__',
	}

	method_order = (
		'__init__',
		'__new__',
		'__call__',
	)

	@staticmethod
	def module_context(route:libroutes.Import):
		"""
		# Given an import route, return the context package
		# and the project module.
		"""
		floor = route.floor()
		if floor is None:
			return None, route
		else:
			context = floor.container

			if not context:
				# route is likely
				return None, floor
			else:
				return context, floor

	def __init__(self, route):
		# initialize the package context
		# used for identifying project local references.
		self.context, self.root = self.module_context(route)
		self.prefix = self.canonical((self.context or self.root).fullname)
		self.stack = []
		self.parameters = {}

	@contextlib.contextmanager
	def cursor(self, name, obj):
		self.stack += (name, obj)
		try:
			yield
		finally:
			del self.stack[-1]

	def is_class_method(self, obj:object,
			getfullargspec=inspect.getfullargspec,
			checks = (
				inspect.ismethod,
				inspect.isbuiltin,
				inspect.isfunction,
				inspect.ismethoddescriptor,
			)
		):
		"""
		# Determine if the given object is a class method.
		"""
		try:
			getfullargspec(obj)
		except TypeError:
			return False

		return any(x(obj) for x in checks)

	def is_class_property(self, obj:object,
			checks = (
				inspect.isgetsetdescriptor,
				inspect.isdatadescriptor,
			)
		):
		"""
		# Determine if the given object is a property.
		# Get-Set Descriptors are also identified as properties.
		"""
		return any(x(obj) for x in checks)

	def is_module(self, obj:object):
		"""
		# Overrideable interface to &inspect.ismodule.
		"""
		return inspect.ismodule(obj)

	def is_module_class(self, module:types.ModuleType, obj:object, isclass=inspect.isclass):
		"""
		# The given object is a plainly defined class that belongs to the module.
		"""
		return isclass(obj) and module.__name__ == obj.__module__

	def is_module_function(self,
			module:types.ModuleType,
			obj:object,
			isroutine=inspect.isroutine
		):
		"""
		# The given object is a plainly defined function that belongs to the module.
		"""
		subject = getattr(obj, '__wrapped__', obj)
		return isroutine(subject) and module.__name__ == subject.__module__

	def docstr(self, obj:object):
		"""
		# Variant of &inspect.getdoc that favors tab-indentations.
		"""
		rawdocs = getattr(obj, '__doc__', None)

		if rawdocs is None:
			return None
		lines = rawdocs.split('\n')

		# first non-empty line is used to identify
		# the indentation level of the entire string.
		for fl in lines:
			if fl.strip():
				break

		if fl.startswith('\t'):
			indentation = len(fl) - len(fl.lstrip('\t'))
			return '\n'.join([
				x[indentation:] for x in lines
			])
		else:
			# assume no indentation and likely single line
			return rawdocs

	if hasattr(inspect, 'signature'):
		signature_kind_mapping = {
			inspect.Parameter.POSITIONAL_ONLY: 'positional',
			inspect.Parameter.POSITIONAL_OR_KEYWORD: None, # "default"
			inspect.Parameter.KEYWORD_ONLY: 'keyword',
			inspect.Parameter.VAR_POSITIONAL: 'variable',
			inspect.Parameter.VAR_KEYWORD: 'keywords',
		}

		def signature(self, obj:object, getsig=inspect.signature):
			"""
			# Overridable accessor to &inspect.getfullargspec.
			"""
			return getsig(obj)
	else:
		def signature(self, obj:object, getsig=inspect.getfullargspec):
			"""
			# Overridable accessor to &inspect.getfullargspec.
			"""
			sig = getsig(obj)

	def addressable(self, obj:object, getmodule=inspect.getmodule):
		"""
		# Whether the object is independently addressable.
		# Specifically, it is a module or inspect.getmodule() not return None
		# *and* can `obj` be found within the module's objects.

		# The last condition is used to prevent broken links.
		"""
		return self.is_module(obj) or getmodule(obj) is not None

	@functools.lru_cache(64)
	def canonical(self, name:str, Import=libroutes.Import.from_fullname):
		"""
		# Given an arbitrary module name, rewrite it to use the canonical
		# name defined by the package set (package of Python packages).

		# If there is no canonical package name, return &name exactly.
		"""
		return libfactor.canonical_name(Import(name))

	def address(self, obj:object, getmodule=inspect.getmodule):
		"""
		# Return the address of the given object; &None if unknown.
		"""

		if self.is_module(obj):
			# object is a module.
			module = obj
			path = (self.canonical(module.__name__), None)
		else:
			module = getmodule(obj)
			objname = getattr(obj, '__name__', None)
			path = (self.canonical(module.__name__), objname)

		return path

	def origin(self, obj:object):
		"""
		# Decide the module's origin; local to the documentation site, Python's
		# site-packages (distutils), or a Python builtin.
		"""
		module, path = self.address(obj)

		if module == self.prefix or module.startswith(self.prefix+'.'):
			pkgtype = 'context'
		else:
			m = libroutes.Import.from_fullname(module).module()
			if 'site-packages' in getattr(m, '__file__', ''):
				# *normally* distutils; likely from pypi
				pkgtype = 'distutils'
			else:
				pkgtype = 'builtin'

		return pkgtype, module, path

	@functools.lru_cache(32)
	def project(self, module:types.ModuleType, _get_route = libroutes.Import.from_fullname):
		"""
		# Return the project information about a particular module.

		# Returns `None` if a builtin, an unregistered package, or package without a project
		# module relative to the floor.
		"""
		route = _get_route(module.__name__)

		project = None
		if hasattr(module, '__loader__'):
			d = None
			try:
				d = pkg_distribution(module.__loader__)
			except (AttributeError, ImportError):
				# try Route.project() as there is no pkg_distribution
				pass
			finally:
				if d is not None:
					return {
						'name': d.project_name,
						'version': d.version,
					}

		return getattr(route.project(), '__dict__', None)

def _xml_object(query, name, obj):
	yield from serialization.prefixed(name,
		serialization.switch('py:').object(obj),
	)

def _xml_parameter(query, parameter):
	if parameter.annotation is not parameter.empty:
		yield from _xml_object(query, 'annotation', parameter.annotation)

	if parameter.default is not parameter.empty:
		yield from _xml_object(query, 'default', parameter.default)

def _xml_signature_arguments(query, signature, km = {}):
	if signature.return_annotation is not signature.empty:
		yield from _xml_object(query, 'return', signature.return_annotation)

	for p, i in zip(signature.parameters.values(), range(len(signature.parameters))):
		yield from libxml.element('parameter',
			_xml_parameter(query, p),
			('identifier', p.name),
			('index', str(i)),
			# type will not exist if it's a positiona-or-keyword.
			('type', query.signature_kind_mapping[p.kind]),
		)

def _xml_call_signature(query, obj, root=None):
	global itertools

	try:
		sig = query.signature(obj)
	except ValueError as err:
		# unsupported callable
		s = serialization.switch('py:')
		yield from s.error(err, obj, set())
	else:
		yield from _xml_signature_arguments(query, sig)

def _xml_type(query, obj):
	# type reference
	typ, module, path = query.origin(obj)
	yield from libxml.element('reference', (),
		('source', typ),
		('factor', module),
		('name', path)
	)

def _xml_doc(query, obj, prefix):
	doc = query.docstr(obj)
	if doc is not None:
		if False:
			yield from libxml.element('doc', libxml.escape_element_string(doc),
				('xml:space', 'preserve')
			)
		else:
			yield from libxml.element('doc',
				libtext.XML.transform('e:', doc, identify=prefix.__add__),
			)

def _xml_import(query, context_module, imported, *path):
	mn = imported.__name__

	return libxml.element("import", None,
		('xml:id', '.'.join(path)),
		('identifier', path[-1]),
		('name', query.canonical(mn)),
	)

def _xml_source_range(query, obj):
	try:
		lines, lineno = inspect.getsourcelines(obj)
		end = lineno + len(lines)

		return libxml.element('source', None,
			('unit', 'line'),
			('start', str(lineno)),
			('stop', str(end-1)),
		)
	except (TypeError, SyntaxError, OSError):
		return libxml.empty('source')

def _xml_function(query, method, qname, ignored={
			object.__new__.__doc__,
			object.__init__.__doc__,
		}
	):
	subject = getattr(method, '__wrapped__', method)
	is_wrapped = subject is not method

	yield from _xml_source_range(query, subject)
	if query.docstr(subject) not in ignored:
		yield from _xml_doc(query, subject, qname+'.')
	yield from _xml_call_signature(query, subject, method)

def _xml_class_content(query, module, obj, name, *path,
		chain=itertools.chain.from_iterable
	):
	yield from _xml_source_range(query, obj)
	yield from _xml_doc(query, obj, name+'.')

	rtype = functools.partial(_xml_type, query)
	yield from libxml.element('bases',
		chain(map(rtype, obj.__bases__)),
	)

	yield from libxml.element('order',
		chain(map(rtype, inspect.getmro(obj))),
	)

	aliases = []
	class_dict = obj.__dict__
	class_names = list(class_dict.keys())
	class_names.sort()

	for k in sorted(dir(obj)):
		qn = '.'.join(path + (k,))

		if k in query.class_ignore:
			continue

		try:
			v = getattr(obj, k)
		except AttributeError as err:
			# XXX: needs tests
			s = serialization.switch('py:')
			yield from s.error(err, obj, set())

		if query.is_class_method(v):
			if v.__name__.split('.')[-1] != k:
				# it's an alias to another method.
				aliases.append((qn, k, v))
				continue
			if k not in class_names:
				# not in the immediate class' dictionary? ignore.
				continue

			# Identify the method type.
			if isinstance(v, classmethod) or k == '__new__':
				mtype = 'class'
			elif isinstance(v, staticmethod):
				mtype = 'static'
			else:
				# regular method
				mtype = None

			with query.cursor(k, v):
				yield from libxml.element('method', _xml_function(query, v, qn),
					('xml:id', qn),
					('identifier', k),
					('type', mtype),
				)
		elif query.is_class_property(v):
			local = True
			vclass = getattr(v, '__objclass__', None)
			if vclass is None:
				# likely a property
				if k not in class_names:
					local = False
			else:
				if vclass is not obj:
					local = False

			if local:
				with query.cursor(k, v):
					pfunc = getattr(v, 'fget', None)
					yield from libxml.element(
						'property', chain([
							_xml_source_range(query, pfunc) if pfunc is not None else (),
							_xml_doc(query, v, qn+'.'),
						]),
						('xml:id', qn),
						('identifier', k),
					)
		elif query.is_module(v):
			# handled the same way as module imports
			with query.cursor(k, v):
				yield from _xml_import(query, module, v, qn)
		elif isinstance(v, type):
			# XXX: Nested classes are not being properly represented.
			# Visually, they should appear as siblings in the formatted representation,
			# but nested physically.
			if v.__module__ == module and v.__qualname__.startswith(obj.__qualname__+'.'):
				# Nested Class; must be within.
				yield from _xml_class(query, module, x, path + (x.__qualname__,))
			else:
				# perceive as class data
				pass
		else:
			# data
			pass

	for qn, k, v in aliases:
		with query.cursor(k, v):
			yield from libxml.element('alias', None,
				('xml:id', qn),
				('identifier', k),
				('address', v.__name__),
			)

def _xml_class(query, module, obj, *path):
	name = '.'.join(path)
	with query.cursor(path[-1], path[-1]):
		yield from libxml.element('class',
			_xml_class_content(query, module, obj, name, *path),
			('xml:id', name),
			('identifier', path[-1]),
		)

def _xml_context(query, package, project, getattr=getattr):
	if package and project:
		pkg = package.module()
		prj = project.module()
		yield from libxml.element('context', (),
			('context', query.prefix),
			('path', query.canonical(pkg.__name__)),
			('system.path', os.path.dirname(pkg.__file__)),
			('project', getattr(prj, 'name', None)),
			('identity', getattr(prj, 'identity', None)),
			('icon', getattr(prj, 'icon', None)),
			('fork', getattr(prj, 'fork', None)),
			('contact', getattr(prj, 'contact', None)),
			('controller', getattr(prj, 'controller', None)),
			('abstract', getattr(prj, 'abstract', '')),
		)

def _xml_module(query, factor_type, route, module, compressed=False):
	lc = 0
	ir = route
	if module.__factor_composite__:
		sources = libfactor.sources(ir).tree()[1]
	else:
		sources = [libroutes.File.from_absolute(module.__file__)]

	for route in sources:
		if compressed:
			with route.open('rb') as src:
				h = hashlib.sha512()
				x = lzma.LZMACompressor(format=lzma.FORMAT_ALONE)
				cs = bytearray()

				data = src.read(512)
				lc += data.count(b'\n')
				h.update(data)
				cs += x.compress(data)
				while len(data) == 512:
					data = src.read(512)
					h.update(data)
					cs += x.compress(data)

				hash = h.hexdigest()
				cs += x.flush()
		else:
			if route.exists():
				with route.open('rb') as src:
					cs = src.read()
					lc = cs.count(b'\n')
					hash = hashlib.sha512(cs).hexdigest()
			else:
				hash = ""
				cs = b""
				lc = 0

		yield from libxml.element('source',
			itertools.chain(
				libxml.element('hash',
					libxml.escape_element_string(hash),
					('type', 'sha512'),
					('format', 'hex'),
				),
				libxml.element('data',
					libxml.escape_element_bytes(codecs.encode(cs, 'base64')),
					('type', 'application/x-lzma'),
					('format', 'base64'),
				),
			),
			('path', str(route)),
			# inclusive range
			('start', 1),
			('stop', str(lc)),
		)

	if factor_type == 'chapter':
		with open(module.__file__, 'r', encoding='utf-8') as f:
			d = f.read()
		module.__doc__ = d
		yield from _xml_doc(query, module, '')
		module.__doc__ = ''
	else:
		yield from _xml_doc(query, module, 'factor..')

	# accumulate nested classes for subsequent processing
	documented_classes = set()

	if hasattr(module, '__factor_xml__') and module.__factor_xml__ is not None:
		# Override used by composites.
		xml = module.__factor_xml__
		if xml:
			root = xml.getroot()
			if root is not None:
				mod_element = root.find('f:module', namespaces)
				if mod_element is not None:
					from ..xml import lxml
					for x in mod_element.iterchildren():
						yield lxml.etree.tostring(x)
	else:
		for k in sorted(dir(module)):
			if k.startswith('__'):
				continue
			v = getattr(module, k)

			if query.is_module_function(module, v):
				yield from libxml.element('function', _xml_function(query, v, k),
					('xml:id', k),
					('identifier', k),
				)
			elif query.is_module(v):
				yield from _xml_import(query, module, v, k)
			elif query.is_module_class(module, v):
				yield from _xml_class(query, module, v, k)
			else:
				yield from libxml.element('data',
					_xml_object(query, 'object', v),
					('xml:id', k),
					('identifier', k),
				)

def _submodules(query, route, module, element='subfactor'):
	for typ, l in zip(('package', 'module'), route.subnodes()):
		for x in l:
			sf = x.module()
			if sf is not None:
				noted_type = getattr(sf, '__type__', None)
				noted_icon = getattr(sf, '__icon__', None)
			else:
				noted_type = 'error'
				noted_icon = ''

			yield from libxml.element(element, (),
				('type', noted_type),
				('icon', noted_icon),
				('container', 'true' if typ == 'package' else 'false'),
				('identifier', x.basename),
			)
	else:
		# Used by documentation packages to mimic Python modules.
		mods = getattr(module, '__submodules__', ())
		for x in mods:
			yield from libxml.element(element, (),
				('type', 'module'),
				('identifier', x),
			)

	if element == 'subfactor':
		# Composite parts are subfactors too.
		if module.__factor_composite__:
			source_factors = libfactor.sources(route)

			for x in source_factors.tree()[1]:
				path = '/'.join(x.points)
				yield from libxml.element(element, (),
					('type', 'source'),
					('path', path),
					('identifier', x.points[-1]),
				)

		# conditionally for cofactor build.
		if route.container:
			# build out siblings
			yield from _submodules(query, route.container, route.container.module(), 'cofactor')

# function set for cleaning up the profile data keys for serialization.
profile_key_processor = {
	'call': lambda x: x[0] if x[1] != '<module>' else 0,
	'outercall': lambda x: ':'.join(map(str, x)),
	'test': lambda x: x.decode('utf-8'),
	'area': str,
}

def emit(fs, key, iterator):
	r = fs.route(key)
	r.init('file')

	with r.open('wb') as f:
		# the xml declaration prefix is not written.
		# this allows stylesheet processing instructions
		# to be interpolated without knowning the declaration size.
		f.writelines(iterator)

def document(query:Query, route:libroutes.Import, module:types.ModuleType, metrics:typing.Mapping=None):
	"""
	# Yield out a module element for writing to an XML file exporting the documentation,
	# data, and signatures of the module's content.
	"""
	global libxml

	cname = query.canonical(route.fullname)
	basename = cname.split('.')[-1]

	package = route.floor()
	if package is None:
		project = None
	else:
		project = package / 'project'

	coverage = query.parameters.get('coverage')
	if coverage is not None:
		# Complete coverage data.
		untraversed = coverage.pop('untraversed', '')
		traversed = coverage.pop('traversed', '')
		traversable = coverage.pop('traversable', '')
		# instrumentation coverage data.
		fc = coverage.pop('full_counters', None)
		zc = coverage.pop('zero_counters', None)

		data = devxml.Metrics.serialize_coverage(serialization, coverage, prefix="coverage..")

		ntravb = len(traversable)
		ntravd = len(traversed)

		coverage = serialization.element(
			'coverage', data,
			('untraversed', str(untraversed)),
			('traversed', str(traversed)),
			('traversable', str(traversable)),

			('n-traversed', ntravd),
			('n-traversable', ntravb),
		)
	else:
		coverage = ()

	profile = query.parameters.get('profile')
	if profile is not None:
		# Complete measurements. Parts are still going to be referenced.
		profile = serialization.element('profile',
			devxml.Metrics.serialize_profile(serialization, profile, keys=profile_key_processor, prefix="profile.."),
		)
	else:
		profile = ()

	try:
		if hasattr(module, '__file__'):
			factor_type = getattr(module, '__factor_type__', 'module')

			if factor_type == 'chapter':
				ename = 'chapter'
			else:
				ename = 'module'
		else:
			factor_type = 'namespace'

		content = libxml.element(ename,
			_xml_module(query, factor_type, route, module),
			('identifier', basename),
			('name', cname),
		)
	except Exception as error:
		# When module is &None, an error occurred during import.
		factor_type = 'factor'

		# Serialize the error as the module content if import fails.
		content = libxml.element('module',
			serialization.prefixed('error',
				serialization.switch('py:').object(error),
			),
			('identifier', basename),
			('name', cname),
		)

	tests = ()
	if metrics is not None:
		# Acquire relevant test reports.
		# Project holds the full set, and each 'tests' package
		# contains their relevant results along with the module
		# containing the test.

		if factor_type == 'project':
			# full test report
			tests = metrics.get(b'tests:'+str(package).encode('utf-8'))
			if tests is not None:
				tests = pickle.loads(tests)
				tests = serialization.prefixed('test',
					devxml.Test.serialize(serialization, tests)
				)
		else:
			if factor_type == 'tests':
				include_tests = True
			else:
				try:
					include_tests = getattr(route.container.module(), '__type__', None) == 'tests'
				except AttributeError:
					include_tests = False

			if include_tests:
				# test report for the package
				tests = metrics.get(b'tests:'+str(package).encode('utf-8'))
				if tests is not None:
					tests = pickle.loads(tests)
					tests = serialization.prefixed('test',
						devxml.Test.serialize(serialization, {
								k: v for k, v in tests.items()
								if str(k).startswith(cname)
							}
						)
					)

		if tests is None:
			tests = ()

	yield from libxml.element('factor',
		itertools.chain(
			_xml_context(query, package, project),
			_submodules(query, route, module),
			coverage,
			profile,
			tests,
			content,
		),
		('version', '0'),
		('name', cname),
		('identifier', basename),
		('path', (
			None if '__factor_path__' not in module.__dict__
			else module.__factor_path__
		)),
		('depth', (
			None if '__directory_depth__' not in module.__dict__
			else (module.__directory_depth__ * '../')
		)),
		('type', factor_type),
		('xmlns:xlink', 'http://www.w3.org/1999/xlink'),
		('xmlns:py', 'http://fault.io/xml/python'),
		('xmlns:l', 'http://fault.io/xml/literals'),
		('xmlns:e', 'http://fault.io/xml/text'),
		('xmlns', 'http://fault.io/xml/factor'),
	)

if __name__ == '__main__':
	# structure a single module
	import sys
	r = libroutes.Import.from_fullname(sys.argv[1])
	w = sys.stdout.buffer.write
	try:
		w(b'<?xml version="1.0" encoding="utf-8"?>')
		i = document(Query(r), r)
		for x in i:
			w(x)
		w(b'\n')
		sys.stdout.flush()
	except:
		import pdb
		pdb.pm()
