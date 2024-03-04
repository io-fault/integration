"""
# Interface for construction context build cache.
"""
from fault.context import tools
from fault.system import files

class Directory(object):
	"""
	# A filesystem directory managing the build cache of a project set.
	"""
	retained = None
	def __init__(self, route:files.Path):
		self.route = route

	def select(self, project, factor, key) -> files.Path:
		"""
		# Retrieve the route to the work directory for the project's factor.
		"""
		return self.route/project/factor/str(hash(key))

class Persistent(Directory):
	"""
	# Cache directory interface for builds whose cache is expected to be reused.

	# Uses a hashed-key path directory to store and recall entries.
	"""

	retained = True

	@tools.cachedproperty
	def resource(self):
		from fault.route.hash import Segmentation, Directory
		s = Segmentation.from_identity('fnv1a_64', depth=1, length=4)
		return Directory(s, self.route)

	def select(self, project, factor, key):
		prefix = (str(project) + '[' + str(factor) + ']:').encode('utf-8')
		return self.resource.allocate(prefix + key, filename=str)

class Transient(Directory):
	"""
	# Cache directory interface for builds whose cache is expected to be removed.

	# Uses an in memory index to recall positioning and counters to allocate new entries.
	"""

	retained = False

	@tools.cachedproperty
	def counters(self):
		import collections
		import itertools
		return collections.defaultdict(itertools.count)

	@tools.cachedproperty
	def index(self):
		return dict()

	def select(self, project, factor, key):
		project = str(project)
		factor = str(factor)

		if (project, factor, key) not in self.index:
			cid = next(self.counters[project])
			work = self.route/project/str(cid)
			self.index[(project, factor, key)] = work

		return self.index[(project, factor, key)]
