"""
# &.llvm.xslt access library.
"""
from ..xml import libfactor as xmlfactor
from . import xslt

xslt_document, transformation = xmlfactor.xslt(xslt)

def transform(path, **params):
	global transformation
	input = xmlfactor.readfile(path)
	return input, transformation(input, **{k:transformation.strparam(v) for k, v in params.items()})
