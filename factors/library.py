"""
Project development interface for software engineers.
"""
import contextlib
import functools

from . import extension
from .core import roles
from ..routes import library as libroutes

class Factor(tuple):
	"""
	The abstract factor that makes up part of a product.
	Essentially, the route and factor type with respect to construction,
	but also higher level interfaces for supporting construction.
	"""
	__slots__ = ()

	@classmethod
	def from_module(Class, module):
		mt = getattr(module, '__type__', 'python-module')
		return Class((mt, libroutes.Import.from_fullname(module.__name__)))

	@classmethod
	def from_fullname(Class, path, Import=libroutes.Import.from_fullname):
		i = Import(path)
		module = i.module()
		mt = getattr(module, '__type__', 'python-module')
		return Class((mt, i))

	@property
	def type(self):
		"The module's `__type__` attribute."
		return self[0]

	@property
	def route(self):
		"The route to the module."
		return self[1]

	@property
	def source_route(self):
		return (self[1].file().container / 'src')

	@staticmethod
	def _canonical_path(route):
		x = route
		while x.points:
			m = x.module()
			mt = getattr(m, '__type__', None)
			if mt == 'context':
				yield getattr(m, '__canonical__', None) or x.identity
			else:
				yield x.identity
			x = x.container

	@property
	@functools.lru_cache(32)
	def name(self, list=list, reversed=reversed):
		"""
		The canonical factor name.
		"""
		l = list(self._canonical_path(self[1]))
		return '.'.join(reversed(l))

	def sources(self):
		"The full set of source files of the factor."
		if self.type == 'extension':
			#srcdir = extension.extension_sources(self.route.module())
			#fr = libroutes.File.from_absolute(srcdir)
			fr = self.source_route
			return fr.tree()[1]
		else:
			return [libroutes.File.from_absolute(self.route.module().__file__)]

class Project(object):
	"""
	A unit containing targets to be constructed or processed.
	Provides access to project information and common project operations.

	The project's outermost package module must identify itself as the bottom
	in order for &Project to function properly.
	"""

	def __init__(self, route):
		self.route = route
		self.directory = self.route.file().container

	@classmethod
	def from_module(Class, module, Import = libroutes.Import):
		"Return the &Project instance for the given module path."
		r = Import.from_module(module)
		return Class(r.bottom())

	@property
	def information(self):
		"The package's project module. Provides branch information and identity."
		pim = self.route / 'project'
		return pim.module()

	@property
	def qid(self):
		"The package's qualified identity. Uniquely identifies the project and variant."
		pi = self.information
		return '#'.join((pi.identity, pi.fork))

	def initialize(self, role='factor'):
		"""
		Initialize the project so that it may be usable and ready for installation.

		This method will perform the necessary compilation tasks for a production installation.
		"""
		pass

	def validate(self):
		"""
		Validate the functionality of the project.

		This method initializes the project for a "test" role and performs all available tests.
		It does *not* perform coverage analysis.
		"""
		self.initialize('test')
		self.test('test')
		self.test()

	def test(self, role='factor'):
		"""
		Perform the project's tests for the given role.
		"""

	def release(self):
		"""
		Modify the package to become a release.
		"""
