#!/usr/bin/env fault-tool cc-adapter
##

[protocol]:
	: http://if.fault.io/project/integration.vectors

[factor-type]:
	: http://if.fault.io/factors/text

[integration-type]:
	: chapter
	# Identical to chapter.
	# However, used to identify special integration cases.
	: manual

##
# Parse the kleptic text into JSON.
-parse-text-1:
	: "parse-text" - -
	: [unit File]
	: [source File]
	: format [language].[dialect]
	: context [factor-context]
	: project [project-name]
	: factor [factor-path]

##
# Copy the directory tree to the factor image location.
-store-chapter-1:
	: "clean-json" - -
	: [factor-image File]
	: [unit-directory File]
	: format directory.tree
	: intention [fv-intention]
