#!/usr/bin/env fault-tool form-vector
##

[protocol]:
	: http://if.fault.io/project/integration.vectors

[unit-suffix]:
	# No suffix for archived images.
	fv-form-delineated: ""
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

-gcc-diagnostics:
	: -fmax-errors=[error-limit env.ERRLIMIT]
	: -fdiagnostics-color=always
	: -w
	: -W[-gcc-warnings]
	: -Werror=[-gcc-errors]

-gcc-warnings:
	: duplicate-decl-specifier
	: format
	: missing-attributes
	: main

-gcc-errors:
	: implicit
	: uninitialized
	: null-dereference
	: init-self
	: return-type

-clang-diagnostics:
	: -fmax-errors=[error-limit env.ERRLIMIT]
	: -fcolor-diagnostics -fansi-escape-codes
	: -Wno-everthing
	: -W[-clang-warnings]
	: -Werror=[-clang-errors]

-clang-warnings:
	: extra-tokens
	: format
	: four-char-constants
	: ignored-attributes
	: incompatible-sysroot
	: int-conversion
	: long-long
	: macro-redefined
	: main
	: main-return-type

-clang-errors:
	: implicit-function-declaration
	: implicit-int
	: uninitialized
	: null-dereference
	: invalid-noreturn
	: invalid-offsetof

-debug:
	: -g
-profile:
	: -pg
-coverage:
	: --coverage
-optimization-level:
	fv-intention-debug: -O0
	fv-intention-profile: -O2
	fv-intention-optimal: -O2
	fv-intention-coverage: -O0

-includes:
	: -I[http://if.fault.io/factors/lambda.sources#source-paths]
	: -isystem [-system-includes]

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
	# When pie-form is requested, use when compiling archives.
	it-archive:
		fv-form-pie: -fPIE
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

-library-directories:
	: [http://if.fault.io/factors/system.directory#factor-image]

-library-names:
	: [http://if.fault.io/factors/system.library-name#factor-image]

-library-factors:
	: [http://if.fault.io/factors/system.library#factor-image-name]

-archive-factors:
	: [http://if.fault.io/factors/system.archive#factor-image]

# Non-component requirements.
-linker-requirements:
	: -L[-system-library-directories]
	: -l[-system-libraries]
	: -L[-library-directories]
	: -l[-library-names]
	: -l:[-library-factors]
	# Non-integrated archives.
	: -l:[-archive-factors]

-compile-header:
	: [-languages]
	: -D[-system-defines]
	: [null]

-compile-source:
	# Sources
	: [-languages]
	: [-dialects]
	: -D[-system-defines]
	: [source File]

-header-switch:
	dialect-header: [-compile-header]
	!: [-compile-source]

##
# Primary compilation constructor.
-cc-compile-1:
	!: "compile-source" - -
	: -c

	fv-intention-debug:
		: [-debug]
	fv-intention-coverage:
		: [-coverage]
	fv-intention-profile:
		: [-profile]

	: [-optimization-level]

	: [-language-injections]
	: [-intention-injections]

	# Target defined options.
	: [-system-cc-options]

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
	: -Xlinker -rpath=[http://if.fault.io/factors/system.directory#factor-image]

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
	fv-intention-coverage: --coverage
	fv-intention-profile: -pg

	: [-elf-legacy-format-control]
	: [-elf-itype-switch]
	: [-elf-rpath]

	: -o [factor-image File]
	: -Wl,-(
	: [-system-context]
	: [-linker-requirements]
	: [units File]
	: -Wl,-)

-llvm-ld-elf:
	: "link-elf-image" - -
	verbose: -v
	fv-intention-coverage: --coverage
	fv-intention-profile: -pg

	: [-elf-legacy-format-control]
	: [-elf-itype-switch]
	: [-elf-rpath]

	: [-system-context]
	: [-linker-requirements]

	: -o [factor-image File]
	: [units File]

-macho-itype-switch:
	it-executable:
		: -Wl,-execute

	it-library:
		: -Wl,-dylib

	it-extension:
		: -Wl,-bundle,-undefined,dynamic_lookup

-macho-rpath:
	# Requirements of factor.
	: -Xlinker -rpath -Xlinker [http://if.fault.io/factors/system.directory#factor-image]

-apple-ld-macho:
	: "link-macho-image" - -
	verbose: -v
	: -shared
	: [-macho-itype-switch]
	: [-system-context]
	: [-macho-rpath]
	: [-linker-requirements]

	: -o [factor-image File]
	: [units File]

-archive-delineated:
	: "archive-tree" - -
	: [factor-image File]
	: [unit-directory File]

-cc-link-1:
	# Copy directory tree to image location.
	fv-form-delineated: [-archive-delineated]
	# Usually defined in .target
	!: [-cc-select-ld-interface]
