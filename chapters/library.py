"""
Factors library providing high level access to structuring and formatting the
factors that make up a product.
"""
import typing

from ..routes import library as libroutes
from ..filesystem import library as libfs
from ..text import library as libtext
from ..system import libfactor
from ..xml import libfactor as xmlfactor
from ..xml import library as libxml

namespaces = {
	'xlink': 'http://www.w3.org/1999/xlink',
	'inspect': 'https://fault.io/xml/inspect#set',
}

def extract_inspect(xml, href='{%s}href' %(namespaces['xlink'],)):
	"""
	Load the factor of an inspect role run.

	[Effects]

	/Product
		A pair, the former being the command parameters and the latter
		being the set of sources.
	"""
	global namespaces

	e = xml.getroot()

	# Stored parameters of the link. (library.set)
	params = e.find("./inspect:parameters", namespaces)
	if params is not None:
		data, = params
		s = libxml.Data.structure(data)
	else:
		s = None

	# Source file.
	sources = e.findall("./inspect:source", namespaces)
	sources = [libroutes.File.from_absolute(x.attrib[href].replace('file://', '', 1)) for x in sources]

	return s, sources

def factors(package:str) -> typing.Tuple[
		libroutes.Import,
		typing.Sequence[libroutes.Import],
		typing.Sequence[libroutes.Import]
	]:
	"""
	Construct and return the factors (modules and packages) contained within
	the given &package string.

	[ Effects ]
	/Product
		`(root, (packages, modules))`; where root is the &package parameter
		as an &libroutes.Import.

	All objects are &..routes.library.Import instances pointing to the module.

	[ Parameters ]

	/package
		The path to the package.
	"""
	global libroutes
	root = libroutes.Import.from_fullname(package)
	return (root, root.tree())

def fractions(packages:libroutes.Import) -> typing.Mapping[
		libroutes.Import,
		typing.Sequence[libroutes.Import],
	]:
	"""
	Construct a mapping detailing the factors that consist of a set of fractions.
	Factors that represent the construction of a set of fractions are used to manage
	build targets.

	[Effects]
	/Product
		The constructed mapping. The keys are the &libroutes.Import instances,
		and the values are sequences.

	[Parameters]
	/packages
		The set of factor packages to inspect in order to find the associated fractions.
	"""
	global libfactor
	return {
		x: libfactor.sources(x)
		for x in packages
		if libfactor.composite(x)
	}

from . import xslt
xslt_document, transformation = xmlfactor.xslt(xslt)

def transform(path, **params):
	global transformation
	input = xmlfactor.readfile(path)
	return input, transformation(input, **{k:transformation.strparam(v) for k, v in params.items()})
