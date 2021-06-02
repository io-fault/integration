def instantiate_software(ctxpy, package, subpackage, name, template, type, fault='fault'):
	# Initiialize llvm instrumentation or delineation tooling inside the target context.
	from fault.text.bin import ifst
	ifst.instantiate(
		(ctxpy / package / subpackage / name),
		template,
		type
	)
