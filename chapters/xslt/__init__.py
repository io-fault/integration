__type__ = 'xsl'
from ...development import libxml

class Index(libxml.XPathModule):
	def __init__(self, transform):
		pass

libxml.load()
del libxml
