__type__ = 'xsl'
from ...xml import libfactor
from ...routes import library as libroutes

class Factor(libfactor.XPathModule):
	def reference(self, context, string, split=libroutes.Import.from_attributes):
		"""
		Return a node-set containing the real module path and the attributes following
		the module.
		"""
		route, attributes = split(string)
		module = str(route)
		path = '.'.join(attributes)
		return [module, path]

libfactor.load()
del libfactor
