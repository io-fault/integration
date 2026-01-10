from fault.system import process

def main(inv:process.Invocation) -> process.Exit:
	print('[<> ' + ' '.join(inv.argv) + ']')
