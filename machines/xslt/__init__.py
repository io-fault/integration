"""
# Transformation to &..fault.factors XML for &.bin.inspect output.
"""
from ...xml import libfactor
from ...chronometry import library as libtime
from ...chronometry import metric
from ...text import library as libtext

namespace = 'http://fault.io/xml/factor'
def name(name_string):
	return '{%s}%s' %(namespace, name_string)

class Factor(libfactor.XPathModule):
	"""
	# Support for operations that would be difficult in some fashion if written in XSLT.
	"""
	from ...xml import libfactor

	def resolve_origin(self, context, string):
		"""
		# Return a qualified name to the factor and its subfactor that is referred to by an
		# origin.
		"""
		return [None]

	@staticmethod
	def clean_comment(string):
		"""
		# Remove decorations and leading spaces from a comment.
		"""
		return '\n'.join([x.lstrip('/* \t').rstrip() for x in ''.join(map(str, string)).split('\n')])

	def structure_comment(self, context, string):
		"""
		"""
		start = b'<f:doc xmlns:f="http://fault.io/xml/factor" xmlns:txt="http://fault.io/xml/text">'

		ftxt = self.clean_comment(string)
		if not ftxt:
			return ()

		xml = b''.join(libtext.XML.transform('txt:', ftxt, encoding='utf-8'))
		if xml:
			return self.libfactor.etree.XML(start + xml + b'</f:doc>')
		else:
			return ()

__factor_type__ = 'xml'
__factor_dynamics__ = 'executable'
