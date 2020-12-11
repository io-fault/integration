from fault.system import execution

def instantiate_software(ctxpy, package, subpackage, name, template, type, fault='fault'):
	# Initiialize llvm instrumentation or delineation tooling inside the target context.
	command = [
		"python3", "-m",
		fault+'.text.bin.ifst',
		str(ctxpy / package / subpackage / name),
		str(template), type,
	]

	pid, status, data = execution.effect(execution.KInvocation(sys.executable, command))
	if status != 0:
		sys.stderr.write("! ERROR: tool software instantiation failed\n")
		sys.stderr.write("\t/command\n\t\t" + " ".join(command) + "\n")
		sys.stderr.write("\t/status\n\t\t" + str(status) + "\n")

		sys.stderr.write("\t/message\n")
		sys.stderr.buffer.writelines(b"\t\t" + x + b"\n" for x in data.split(b"\n"))
		raise SystemExit(1)
