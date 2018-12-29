"""
# Executable access to llvm.xslt.
"""
import lxml.etree
import sys

from fault.system import python
from fault.xml import libfactor

if __name__ == '__main__':
	cmd, target_xml_path = sys.argv
	xd, xslt = libfactor.xslt(python.Import.from_fullname(__package__).module())
	del xd
	i, out = libfactor.transform(xslt, target_xml_path)
	del i
	out.write(sys.stdout.buffer)
