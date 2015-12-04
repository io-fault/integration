"""

"""
import typing
from ..routes import library as libroutes

def factors(package:str, Route=libroutes.Import.from_fullname) -> (
		libroutes.Import,
		typing.Sequence[libroutes.Import],
		typing.Sequence[libroutes.Import]
	):
	"""
	Construct and return the factors (modules and packages) contained within
	the given &package string.

	[ Return ]

		# root
		# packages
		# modules

	Returns a tuple in the form: `(root, [packages], [modules])`.
	All objects are &..routes.library.Import instances pointing to the module.

	[ Parameters ]

	/package
		The path to the package.
	"""

	root = Route(package)
	return (root, root.tree())
