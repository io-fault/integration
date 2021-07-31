#!/usr/bin/env fault-tool cc-adapter
##

[protocol]:
	: http://if.fault.io/project/integration.vectors

[unit-suffix]:
	# No suffix for archived images.
	fv-idelineation: ""
	fv-ianalysis: ""
	# Extension usually required by compiler drivers as
	# -x only accepts PL names, not object file formats.
	!: ".o"

[environment]:
	: ERRLIMIT

[factor-type]:
	: http://if.fault.io/factors/system

[integration-type]:
	: library
	: extension
	: executable
	: archive

[diagnostic-control]:
	: verbose

-debug:
	: -g
-profile:
	: -pg
-coverage:
	: --coverage
-optimization-level:
	fv-idebug: -O0
	fv-iprofile: -O2
	fv-ioptimal: -O2
	fv-icoverage: -O0

-includes:
	: -I[http://if.fault.io/factors/lambda.sources#source-paths]
	: -I[-system-includes]

-variants:
	# Variants
	: -DFV_INTENTION=[fv-intention]
	: -DFV_ARCHITECTURE=[fv-architecture]
	: -DFV_SYSTEM=[fv-system]
	!fv-form-void: -DFV_FORM=[fv-form]

-factor-identity:
	# Identification
	: -DF_CONTEXT=[context-path]
	: -DF_PROJECT=[project-name]
	: -DF_FACTOR=[factor-relative-path]
	: -DF_FACTOR_NAME=[factor-name]
	: -DF_PROJECT_PATH=[project-path]
	: -DF_PROJECT_ID=[project-id quoted]

-positioning-format:
	# Position formatting.
	# -fPIE when building an executable, -fPIC for everything else.
	it-executable: -fPIE
	it-archive/fv-form-pie: -fPIE
	!: -fPIC

-languages:
	!: -x [language]

-dialects:
	# clang and gcc want the prefix here.
	# factors/system.type uses a vendor qualified language name.
	language-c:
		: -std=[dialect prefix.iso9899:]
	language-c++:
		: -std=[dialect prefix.iso14882:]
	!: -std=[dialect]

-library-factors:
	: [http://if.fault.io/factors/system.library#factor-image-name]

-archive-factors:
	: [http://if.fault.io/factors/system.archive#image]

# Non-component requirements.
-linker-requirements:
	: -L[-system-library-directory]
	: -l[-system-library]
	: -l:[-library-factors]
	# Non-integrated archives.
	: -l:[-archive-factors]

-analyze:
	: -fmax-errors=[error-limit env.ERRLIMIT]
	: -Wall

-diagnostics-control:
	fv-ianalysis: [-analyze]
	.: -o /dev/null
	!: -w -c

-compile-header:
	: [-languages]
	: [null]

-compile-source:
	# Sources
	: [-languages]
	: [-dialects]
	: [source File]

-header-switch:
	dialect-header: [-compile-header]
	!: [-compile-source]

##
# Primary compilation constructor.
-cc-compile-1:
	fv-ianalysis: "analyze-source" - stderr
	!: "compile-source" - -

	fv-ianalysis: -fsyntax-only
	fv-idebug: [-debug]
	fv-icoverage: [-coverage]
	fv-iprofile: [-profile]
	: [-optimization-level]

	: [-language-injections]
	: [-intention-injections]

	: [-diagnostics-control]

	# Position capability: PIC or PIE.
	: [-positioning-format]

	# Defines.
	: [-factor-identity]
	: [-variants]

	# System includes, lambda sources, and system sources.
	: [-includes]

	# Parameters should be isolated if surrounding fields should be repeated with each item.
	: -o [unit File]

	# Switch header/source compilation.
	: [-header-switch]

-cc-archive-reports:
	: "archive-tree" - -
	: [-fs-archive]

-elf-legacy-format-default:
	: -Wl,--enable-new-dtags,--eh-frame-hdr

-elf-legacy-format-control:
	: [-elf-legacy-format-default]

##
# rpath for both system libraries and requirements.
-elf-rpath:
	# Using -Xlinker form to avoid exception cases.
	: -Xlinker -rpath=[system-library-directory]

	# Requirements of factor.
	: -Xlinker -rpath=[system.library/library-directories]

-elf-itype-switch:
	it-executable:
		: -pie

	it-library:
		: -shared

	it-extension:
		: -shared -Xlinker --unresolved-symbols=ignore-all

-gnu-ld-elf:
	: "link-elf-image" - -
	verbose: -v
	fv-icoverage: --coverage
	fv-iprofile: -pg

	: [-elf-legacy-format-control]
	: [-elf-itype-switch]
	: [-elf-rpath]

	: -o [output File]
	: -Wl,-(
	: [-system-context]
	: [-linker-requirements]
	: [units File]
	: -Wl,-)

-llvm-ld-elf:
	: "link-elf-image" - -
	verbose: -v
	fv-icoverage: --coverage
	fv-iprofile: -pg

	: [-elf-legacy-format-control]
	: [-elf-itype-switch]
	: [-elf-rpath]

	: [-system-context]
	: [-linker-requirements]

	: -o [output File]
	: [units File]

-macho-itype-switch:
	it-executable:
		: -Wl,-execute

	it-library:
		: -Wl,-dylib

	it-extension:
		: -Wl,-bundle,-undefined,dynamic_lookup

-apple-ld-macho:
	: "link-macho-image" - -
	verbose: -v
	: -shared
	: [-macho-itype-switch]
	: [-system-context]
	: [-linker-requirements]

	: -o [factor-image File]
	: [units File]

-cc-link-1:
	# analyze is not addressable by default
	fv-ianalyze: [-archive-units]
	fv-idelineation: [-archive-units]
	# Defined in another file.
	!: [-cc-select-ld-interface]
