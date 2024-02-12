"""
# Module compilation tools.
"""
import ast
import builtins
import typing
import hashlib
import io
import codecs

constant_expression = "%s = %r"

def hash_syntax(source, encoding='utf-8', hi=hashlib.sha3_256, hash_chunks=1024*4):
	h = hi()
	memory = io.BytesIO()
	sw = codecs.getwriter(encoding)(memory)

	for i in range(0, len(source), hash_chunks):
		sw.write(source[i:i+hash_chunks])
		memory.seek(0)
		h.update(memory.read())
		memory.truncate()
	return h.hexdigest()

def mkconstant(name, value, path='/dev/null', lineno=-1):
	"""
	# Create a constant for injection into a module.
	"""

	s = constant_expression % (name, value,)
	p = ast.parse(s, path)
	assert isinstance(p, ast.Module)

	k = p.body[0]
	return k

def inject(tree:ast.Module, constants:typing.Iterable[typing.Tuple[str,str]]):
	"""
	# Inject the &ast.Module, &tree, with module-level assignments provided by &constants.
	"""
	tree.body[0:0] = [mkconstant(*pair) for pair in constants]
	return tree

def compile(factor, source, path, constants):
	"""
	# Compile a module's source injecting a factor identifier and source hash.
	"""
	tree = ast.parse(source, path)
	constants.extend([
		('__factor__', factor),
		('__source_hash__', hash_syntax(source)),
	])
	return inject(tree, constants)
