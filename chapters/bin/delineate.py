"""
# Delineate a text file.
"""
import json

from fault.text.bin import parse
from fault.system import files
from fault.system import process

def main(inv:process.Invocation) -> process.Exit:
	target, source, *defines = inv.args # (output-directory, source-file-path)

	with files.Path.from_path(source).fs_open('r') as f:
		chapter = parse.chapter(f.read())
	root = ('factor', [chapter], {})

	r = files.Path.from_path(target)
	r.fs_mkdir()

	with (r/"elements.json").fs_open('w') as f:
		json.dump(root, f)

	return inv.exit(0)

if __name__ == '__main__':
	process.control(main, process.Invocation.system())
