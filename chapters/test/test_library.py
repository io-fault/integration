from .. import library
from ...xml import lxml

def test_XSLT_access(test):
	pass

open_element = b'<introspection xmlns:xlink="http://www.w3.org/1999/xlink" '
open_element += b'xmlns:data="https://fault.io/xml/data" xmlns="https://fault.io/xml/inspect#set">'

def test_extract_inspect(test):
	"""
	"""
	t = open_element + b'</introspection>'
	xml = lxml.etree.XML(t).getroottree()

	test/library.extract_inspect(xml) == (None, [])

	t = b''
	t += open_element
	t += b'<parameters><data:dictionary/></parameters>'
	t += b'</introspection>'
	xml = lxml.etree.XML(t).getroottree()

	test/library.extract_inspect(xml) == ({}, [])

	t = b''
	t += open_element
	t += b'<parameters><data:dictionary/></parameters>'
	t += b'<source xlink:href="file:///test/f1"/>'
	t += b'<source xlink:href="/test/f2"/>'
	t += b'</introspection>'
	xml = lxml.etree.XML(t).getroottree()

	f1 = libroutes.File.from_absolute('/test/f1')
	f2 = libroutes.File.from_absolute('/test/f2')
	test/library.extract_inspect(xml) == ({}, [f1, f2])

if __name__ == '__main__':
	from ...development import libtest; import sys
	libtest.execute(sys.modules[__name__])
