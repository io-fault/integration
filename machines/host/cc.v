#!/usr/bin/env factor-type http://if.fault.io/factors/meta.vectors
##

[protocol]:
	: http://if.fault.io/project/integration.vectors

[unit-suffix]:
	# No suffix for archived images.
	cc-mode-delineation: ""
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

-context-identity:
	: CC_TYPE=fault
	: CC_PATH=[construction-context-path quoted]

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
	: -Wno-unknown-warning-option
	: -w
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

-optimization-level:
	if-optimal: -O2
	!: -O0

-includes:
	: -I[http://if.fault.io/factors/meta.sources#source-paths]
	: -isystem [-system-includes]
	: -F [http://if.fault.io/factors/system.framework-directory#factor-image]

-variants:
	# Variants
	: -DFV_ARCHITECTURE=[fv-architecture]
	: -DFV_SYSTEM=[fv-system]
	: -DFV_FORM=[fv-form]

-factor-identity:
	# Identification
	: -DF_CONTEXT=[context-path]
	: -DF_PROJECT=[project-name]
	: -DF_FACTOR=[factor-relative-path]
	: -DF_FACTOR_NAME=[factor-name]
	: -DF_PROJECT_PATH=[project-path]
	: -DF_PROJECT_ID=[project-id quoted]
	: -DF_PRODUCT_PATH=[product-path quoted]
	: -DF_FACTOR_IMAGE=[factor-image quoted]

-positioning-format:
	# Position formatting.
	# -fPIE when building an executable, -fPIC for everything else.
	it-executable: -fPIE
	# When pie-form is requested, use when compiling archives.
	it-archive:
		fv-form-pie: -fPIE
	!: -fPIC

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
	: -L[http://if.fault.io/factors/system.library#image-directory]
	: -L[-system-library-directories]
	: -l[-system-libraries]
	: -L[-library-directories]
	: -l[-library-names]
	: -l:[-library-factors]
	: -l:[-archive-factors]

-macho-library-factors:
	: -needed_library [http://if.fault.io/factors/system.library#factor-image]

-macho-framework-directories:
	: -F [http://if.fault.io/factors/system.framework-directory#factor-image]

-macho-framework-names:
	: -framework [http://if.fault.io/factors/system.framework-name#factor-image-name]

-macho-requirements:
	# image-directory is not necessary on macos as ld can link directly against a file
	: -L[-system-library-directories]
	: -l[-system-libraries]
	: -L[-library-directories]
	: -l[-library-names]
	: -Xlinker [-macho-library-factors]
	: -Xlinker [-macho-framework-directories]
	: -Xlinker [-macho-framework-names]
	: [-archive-factors]

-languages:
	!: -x [language]

-dialects:
	# clang and gcc want the prefix here.
	language-c:
		: -std=[dialect prefix.iso9899:]
	language-c++:
		dialect-2023: -std=c++23
		dialect-2020: -std=c++20
		dialect-2017: -std=c++17
		dialect-2014: -std=c++14
		dialect-2011: -std=c++11
		dialect-2003: -std=c++03
		dialect-1998: -std=c++98
		!: -std=[dialect prefix.iso14882:]
	# Unsupported dialect.
	!: -std=[dialect]

-compile-header:
	: [-languages]
	: -D[-system-defines]
	:
		cc-mode-delineation: [source File]
		!: [null]

-compile-source:
	# Sources
	: [-languages]
	: [-dialects]
	: -D[-system-defines]
	: [source File]

-header-switch:
	dialect-header: [-compile-header]
	!: [-compile-source]

-llvm-instrumentation:
	if-coverage:
		: -fprofile-instr-generate -fcoverage-mapping
	if-profile:
		: -fprofile-instr-generate
-llvm-instrumentation-defines:
	: -DF_LLVM_INSTRUMENTATION
-factor-telemetry:
	: -DF_TELEMETRY=""""[telemetry-directory File]""""

##
# Primary compilation constructor.
-cc-compile-1:
	!: "compile-source" - -
	: -c

	: [-optimization-level]
	if-debug:
		: [-debug]

	: [-llvm-instrumentation]
	:
		if-coverage: [-llvm-instrumentation-defines]
		if-profile: [-llvm-instrumentation-defines]
		if-metrics: [-factor-telemetry]

	: [-language-injections]

	# Target defined options.
	: [-system-cc-options]

	# Position capability: PIC or PIE.
	: [-positioning-format]

	# Defines.
	: -D[-context-identity]
	: -DIF_[if-set]
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

-gnu-instrumentation:
	# meta.metrics does not support collecting data from the gnu toolchain.
	if-coverage:
		: --coverage
	if-profile:
		: -pg

-gnu-ld-elf:
	: "link-elf-image" - -
	verbose: -v

	# Rather than guarding, trigger failure with gnu tooling.
	# If LLVM instrumentation is somehow available, continue normally.
	: [-llvm-instrumentation]
	# [-gnu-instrumentation]

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

	: [-llvm-instrumentation]
	: [-elf-legacy-format-control]
	: [-elf-itype-switch]
	: [-elf-rpath]

	: [-system-context]
	: [-linker-requirements]

	: -o [factor-image File]
	: [units File]

-macho-itype-switch:
	it-executable:
		: -execute

	it-library:
		: -dylib

	it-extension:
		: -bundle -undefined dynamic_lookup

-macho-rpath:
	# Requirements of factor.
	: -rpath [http://if.fault.io/factors/system.directory#factor-image]

-apple-ld-macho:
	: "link-macho-image" - -
	verbose: -v
	: -shared

	: [-llvm-instrumentation]
	: -Xlinker [-macho-itype-switch]
	: [-system-context]
	: -Xlinker [-macho-rpath]
	: [-macho-requirements]

	: -o [factor-image File]
	: [units File]

-archive-delineated:
	: "archive-tree" - -
	: [construction-context-path File]
	: [executable-image File]
	: [factor-image File]
	: [unit-directory File]

-cc-link-1:
	# Copy directory tree to image location.
	cc-mode-delineation: [-archive-delineated]
	# Usually defined in .target
	!: [-cc-select-ld-interface]
