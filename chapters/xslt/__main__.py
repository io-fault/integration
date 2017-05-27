"""
# Module execution entry point for performing single transformations.

# Usually used for debugging.
"""

import sys
from ...xml import libfactor
from ...routes import library as libroutes
from ...filesystem import library as libfs
from .. import tools

def index(source):
	structs = libfs.Dictionary.open(source)

	return {
		k.decode('utf-8'): r
		for k, r in structs.references()
	}

if __name__ == '__main__':
	cmd, target_xml_path, *params = sys.argv
	params = dict(zip(params[0::2], params[1::2]))
	xd, xslt = libfactor.xslt(libroutes.Import.from_fullname(__package__).module())
	del xd

	src = params.pop('document_index')
	with libroutes.File.temporary() as tr:
		idx_path = tr / 'index.xml'
		idx_path.store(tools.construct_corpus_map(src, index(src)))

		i, out = libfactor.transform(xslt, target_xml_path, document_index=str(idx_path))
		for x in xslt.error_log:
			if x.message:
				sys.stderr.write(x.message+'\n')
		del i
		out.write(sys.stdout.buffer)
