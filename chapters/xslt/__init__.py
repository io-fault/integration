"""
Primary formatting pipeline for `Structured Factors`.
"""
from ...xml import libfactor
from ...computation import librange
from ...chronometry import library as libtime
from ...chronometry import metric

namespace = 'https://fault.io/xml/factor'
def name(name_string):
	global namespace
	return '{%s}%s' %(namespace, name_string)

RangeSet = librange.Set

class Factor(libfactor.XPathModule):
	"""
	Support for operations that would be difficult in some fashion if written in XSLT.
	"""

	import builtins
	from ...routes import library as libroutes

	def reference(self, context, string, split=libroutes.Import.from_attributes):
		"""
		Return a node-set containing the real module path and the attributes following
		the module.
		"""
		route, attributes = split(string)
		module = str(route)
		path = '.'.join(attributes)
		return [module, path]

	def builtin(self, context, string):
		"""
		Whether or not the given string refers to a builtin.
		"""
		return self.builtins.__dict__.__contains__(string)

	def exception(self, context, string):
		"""
		Whether or not the given string refers to a builtin exception.
		"""
		if self.builtins.__dict__.__contains__(string):
			obj = self.builtins.__dict__[string]
			return isinstance(obj, type) and issubclass(obj, BaseException)
		else:
			return False

	def cache(self, context, *args, coverage=name('coverage')):
		"""
		Cache the coverage information for context specific queries (functions/methods).
		"""
		factor = context.context_node
		cov = factor.find(coverage)
		if cov is None:
			cov = {}

		self.traversed = RangeSet.from_string(cov.get('traversed', ''))
		self.traversable = RangeSet.from_string(cov.get('traversable', ''))
		self.untraversed = RangeSet.from_string(cov.get('untraversed', ''))

		return None

	def untraversed(self, context, *args, source=name('source')):
		"""
		Collect the per-concept untraversed lines.
		"""
		node = context.context_node
		src = node.find(source)

		if src is not None:
			start = src.get('start')
			stop = src.get('stop')
			if start is None or stop is None:
				return []
		else:
			return []

		# source element with start and stop available.
		ir = librange.IRange((int(start), int(stop)))
		rs = RangeSet.from_normal_sequence([ir])
		luntraversed = RangeSet.from_normal_sequence(list(self.untraversed.intersection(rs)))

		return str(luntraversed)

	def summary(self, context, *args,
			source=name('source'), list=list, int=int
		):
		"""
		Collect the per-concept untraversed lines summary data.
		"""
		node = context.context_node
		src = node.find(source)

		if src is not None:
			start = src.get('start')
			stop = src.get('stop')
			if start is None or stop is None:
				return []
		else:
			return []

		start = int(start)
		stop = int(stop)

		# source element with start and stop available.
		rs = RangeSet.from_normal_sequence([librange.IRange((start, stop))])

		traversable = RangeSet.from_normal_sequence(list(self.traversable.intersection(rs)))
		atraversed = RangeSet.from_normal_sequence(list(self.traversed.intersection(traversable)))

		return [str(len(atraversed)), str(len(traversable)), str((stop+1) - start)]

	def duration(self, context, nanoseconds,
			initial='hour',
			units=('minute', 'second', 'millisecond', 'microsecond', 'nanosecond'),
			nte=metric.name_to_exponent,
			abb=metric.abbreviations,
			ustr=lambda ne, ab, x: ab[ne[x]] if x in ne else ' ' + x + 's'
		):
		"""
		Create a string representing the given nanoseconds in a human readable form.
		"""
		ns = int(nanoseconds)
		ns = libtime.Measure(ns)

		out = [(ns.select(initial), initial)]
		ns = ns.decrease(**{initial: out[0][0]})
		for u in units:
			d = ns.select(u, out[-1][1])
			out.append((d, u))
			ns = ns.decrease(**{u: out[-1][0]})

		return ' '.join(('%d%s' % (x[0], ustr(nte, abb, x[1]))) for x in out if x[0] > 0)

__factor_type__ = 'xml.executable'
