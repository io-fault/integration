__type__ = 'xsl'
from ...xml import libfactor

class Index(libfactor.XPathModule):
	def test(self, context):
		print('pass!!')
		return ''

libfactor.load()
del libfactor
