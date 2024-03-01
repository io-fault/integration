"""
# Analyze the &.query.Cursor implementation.
# Currently, somewhat redundant with the route tests, but
# check the functionality with respect to the configured &module.context.
"""
from .. import query as module
from fault.text.io import structure_chapter_text

cursor = None
document_text = "\n".join([
	"! CONTEXT:",
	"\t/protocol/",
	"\t\t&<http://if.fault.io/test>",
	"[ Section Name ]",
	"First paragraph.",
	"",
	"Second paragraph.",
	"[ Objects ]",
	"# Item1",
	"# Item2",
	"- SetItem1",
	"- SetItem2",
	"",
	"Second paragraph.",
	"[ ] Odd Section [ ]",
	"/key/",
	"\tvalue",
	"[ Final Section ]",
	"Last paragraph.",
	"#!/text parameter-data",
	"\tSubtext Paragraph",
	""
])

cursor = module.navigate(structure_chapter_text(document_text))

def test_invalid_selector_single(test):
	parse = module.context.prepare
	test/module.InvalidPath ^ (lambda: list(parse("/section[Section Name]paragraph")))

def test_invalid_selector_all(test):
	parse = module.context.prepare
	test/module.InvalidPath ^ (lambda: list(parse("/section[Section Name]*")))

def test_no_filter_error(test):
	test/module.InvalidPath ^ (lambda: cursor.select("/section?no-such-filter"))

def test_select_query_sanity(test):
	r = cursor.select('/section')
	test/len(r) == 4
	ids = [x[-1]['identifier'] for x in r]
	test/ids == ["Section Name", "Objects", "] Odd Section [", "Final Section"]

def test_select_indexing(test):
	test/cursor.select('/section#1')[0][2]['identifier'] == "Section Name"
	test/cursor.select('/section#2')[0][2]['identifier'] == "Objects"
	test/cursor.select('/section#3')[0][2]['identifier'] == "] Odd Section ["
	test/cursor.select('/section#4')[0][2]['identifier'] == "Final Section"

def test_union(test):
	union = cursor.select("/section[Objects]/set|sequence")
	test/len(union) == 2

	union = cursor.select("/section[Objects]/set#1|sequence#1")
	test/len(union) == 2
	test/union[0][0] == 'set'
	test/union[1][0] == 'sequence'

def test_filter(test):
	def f(element):
		return element[0] == 'section'
	cursor.context.filters['test-section'] = f

	for element in cursor.select('/*?test-section'):
		test/element[0] == 'section'

def test_identifier_escapes(test):
	odd, = cursor.select("/section[\\] Odd Section []")
	test/odd[2]['identifier'] == "] Odd Section ["
