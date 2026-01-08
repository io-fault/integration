"""
# Identify sources and create factor identity indices.
"""
import sys
import hashlib
import collections

from fault.system import process

def main(inv:process.Invocation) -> process.Exit:
	sub, output, *argv = inv.argv

	if sub == 'source':
		assert output == '-'
		h = hashlib.sha256()
		l = 0
		sources = [sys.stdin.buffer]
		for x in argv:
			sources.append(open(x, 'rb'))

		for f in sources:
			data = b'-'
			while data:
				data = f.read(1024*4)
				l += len(data)
				h.update(data)

		hd = h.hexdigest()
		sys.stdout.write(f"{l} {hd}\n")
	elif sub == 'index':
		argv.sort()
		with open(output, 'w') as out:
			for x in argv:
				# File path.
				out.write(str(x))
				with open(x) as f:
					for line in f.readlines():
						out.write('\n\t'+line.strip())
				out.write('\n')
	else:
		sys.stderr.write(f"ERROR: unknown command {sub!r}\n")
		return inv.exit(1)

	return inv.exit(0)
