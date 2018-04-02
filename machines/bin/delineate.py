"""
# Delineate a source file using libclang.

# Delineatation is a two-stage process where a libclang linked binary is executed emitting
# an schema-less XML document that is processed by an XSLT emitting the fragments that
# can then be published.
"""
import sys
import subprocess
from fault.routes import library as libroutes
from fault.system import library as libsys
from fault.xml import libfactor, library as libxml
from fault.development import fragments
from .. import xslt

inner_call = 'f_syntax.bin.llvm'
def main(inv):
	args = inv.args

	# args passed directly forward to inspect
	sp = subprocess.Popen(
		[sys.executable, '-m', inner_call] + args,
		stdin=None,
		stdout=subprocess.PIPE)
	stdout, stderr = sp.communicate()

	isrc = args[-1]

	# stdout being fully buffered is not really desired, but
	# do so for brevity. The XML document needs to be loaded
	# for transformation anyways.
	xd, xt = libfactor.xslt(xslt)
	rtf = xt(libfactor.readstring(stdout))
	factor = rtf.getroot()
	module = factor.xpath("/*/*[local-name()='module']")[0]

	xml = libxml.Serialization()
	i = fragments.source_element(xml, libroutes.File.from_absolute(isrc))
	rs = b''.join(i)
	rsrc = b'<cell xmlns="http://fault.io/xml/fragments">' + rs + b'</cell>'
	source = libfactor.etree.fromstring(rsrc)
	source.nsmap['f'] = source.nsmap[None]

	del source.nsmap[None]
	del rs, i, xml

	module.insert(0, list(source.iterchildren())[0])

	sys.stdout.buffer.writelines(libfactor.etree.tostringlist(rtf, method="xml", encoding="utf-8"))
	sys.exit(0)

if __name__ == '__main__':
	libsys.control(main, libsys.Invocation.system())

