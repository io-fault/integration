from ...xml import libfactor

class Factor(libfactor.XPathModule):
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

libfactor.load('xsl')
