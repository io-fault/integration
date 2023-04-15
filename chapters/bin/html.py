"""
# System command access to &.html rendering functionality.
"""
import sys
import pprint
import pdb
import traceback

from fault.system import process
from fault.system import files
from .. import html

def main(inv:process.Invocation) -> process.Exit:
	src, *styles = inv.argv
	sf = (process.fs_pwd() @ src)

	with sf.fs_open('r') as f:
		doctext = f.read()

	sx = html.xml.Serialization(xml_encoding='utf-8')
	typ = '://if.fault.io/factors/meta.chapter'
	sub = html.PageSubject('https' + typ + '/.http-resource/icon.svg',
		sf.identifier, 'meta.chapter', 'http' + typ
	)

	ctxpath = sf ** 1
	ctxstr = str(ctxpath)
	ctxtyp = '://if.fault.io/factors/meta.directory'
	ctx = html.PageContext(
		'https' + ctxtyp + '/.http-resource/icon.svg',
		ctxstr, 'file://' + ctxstr,
	)

	try:
		head = html.r_head(sx, 'utf-8', styles=[str(process.fs_pwd()@x) for x in styles])
		sys.stdout.buffer.writelines(html.transform(sx, '', 0, sub, ctx, doctext, head=head))
	except:
		p = pdb.Pdb()
		traceback.print_exc()
		sys.stderr.flush()
		p.interaction(None, sys.exc_info()[2])

	return inv.exit(0)
