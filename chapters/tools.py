"""
# Various utilities supporting processing.
"""

def construct_corpus_map(directory, index):
	import itertools
	from ..xml import library as libxml
	content = libxml.element('map',
		itertools.chain.from_iterable(
			libxml.element('item',
				libxml.escape_element_string(str(r)),
				('key', k)
			)
			for k, r in index.items()
		),
		('dictionary', directory),
		('xmlns', 'http://fault.io/xml/filesystem#index'),
	)

	return b''.join(content)
