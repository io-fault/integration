"""
# Transformation to &fault.factors XML for &.bin.inspect output.
"""
from fault.xml import libfactor
from fault.time import library as libtime
from fault.time import metric
from fault.text import library as libtext

from ....factors import fragments

namespace = 'http://fault.io/xml/fragments'
def name(name_string):
	return '{%s}%s' %(namespace, name_string)

class Factor(libfactor.XPathModule):
	"""
	# Support for operations that would be difficult in some fashion if written in XSLT.
	"""

	def resolve_origin(self, context, string):
		"""
		# Return a qualified name to the factor and its subfactor that is referred to by an
		# origin.
		"""
		return [None]

	@staticmethod
	def clean_comment(lines):
		"""
		# Remove decorations and leading spaces from a comment.
		"""
		return fragments.normalize_documentation(lines)

	def structure_comment(self, context, prefix, string):
		"""
		"""
		start = b'<f:doc xmlns:f="' \
			+ namespace.encode('utf-8') \
			+ b'" xmlns:txt="http://if.fault.io/xml/text">'

		if not string:
			return ()

		string = ''.join(string).strip('/* ')
		ftxt = '\n'.join(self.clean_comment(string.split('\n')))
		if not ftxt:
			return ()

		xml = b''.join(
			libtext.XML.transform('txt:', ftxt,
				identify=prefix.__add__,
				encoding='utf-8')
		)
		if xml:
			return libfactor.etree.XML(start + xml + b'</f:doc>')
		else:
			return ()

__factor_domain__ = 'xml'
__factor_type__ = 'executable'
