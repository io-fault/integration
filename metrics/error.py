"""
# Unconditional error tool for construction contexts.

# Provides command argument based control over exit status code and
# standard error output. Used by command constructors to report unconditional failure.
"""
import sys
from fault.vector import recognition
from fault.system import process

required = {
	'-C': ('subfield-replace', 'system-exit-codes'),
	'-c': ('field-replace', 'default-exit-code'),
}

restricted = {}

def main(inv:process.Invocation) -> process.Exit:
	config = {
		'default-exit-code': 1,
		'system-exit-codes': {},
	}
	v = recognition.legacy(restricted, required, inv.argv)
	remainder = recognition.merge(config, v)

	try:
		factor, element, *argv = remainder

		if (factor, element) == ('.', '.'):
			msg = ' '.join(argv)
		elif (factor, element) == ('.', '-'):
			msg = ' '.join(argv) + '\n'
			msg += sys.stdin.read()
		else:
			msg = '.'.join((factor, element)) + ': ' + ' '.join(argv)
	except:
		msg = ' '.join(remainder)
		raise
	finally:
		sys.stderr.write(msg)
		if msg[-1] != '\n':
			sys.stderr.write('\n')

		inv.exit(int(config['default-exit-code']))
