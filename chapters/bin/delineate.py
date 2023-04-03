"""
# Delineate a text file.
"""
import functools
import json

from fault.system import files
from fault.system import process

from fault.text.io import structure_chapter_text, structure_paragraph_element
from .. import query
P = functools.partial(map, structure_paragraph_element)

def main(inv:process.Invocation) -> process.Exit:
	target, source, *defines = inv.args # (output-directory, source-file-path)

	with files.Path.from_path(source).fs_open('r') as f:
		chapter = structure_chapter_text(f.read())

	# Extract CONTEXT.
	context = {}
	q = query.navigate(chapter)
	ctx = q.fork('/admonition[CONTEXT]#1/directory#1')
	for x in ctx.select('*'):
		try:
			p, = P(ctx.select('item[icon]/value/paragraph#1'))
			context['icon'] = p.sole[1]
		except (ValueError, IndexError):
			pass

		try:
			p, = P(ctx.select('item[protocol]/value/paragraph#1'))
			context['protocol'] = p.sole[1]
		except (ValueError, IndexError):
			pass

		try:
			p, = P(ctx.select('item[title]/value/paragraph#1'))
			context['title'] = p.sole[1]
		except (ValueError, IndexError):
			pass

		# Length test iterator.
		break

	root = ('factor', [chapter], {})

	r = files.Path.from_path(target)
	r.fs_mkdir()

	with (r/"elements.json").fs_open('w') as f:
		json.dump(root, f)

	if context:
		with (r/"context.json").fs_open('w') as f:
			json.dump(context, f)

	return inv.exit(0)

if __name__ == '__main__':
	process.control(main, process.Invocation.system())
