/**
	// fault C construction context environment support.
*/
#ifndef _FAULT_LIBC_H_
#define _FAULT_LIBC_H_

#ifdef __APPLE__
	#include <TargetConditionals.h>
#endif

#define _CPP_QUOTE(x) #x
#define STRING_FROM_IDENTIFIER(X) _CPP_QUOTE(X)
#define CONCAT_IDENTIFIER(X, Y) X##Y
#define CONCAT_REFERENCES(X, Y) CONCAT_IDENTIFIER(X,Y)

#define F_TARGET_ARCHITECTURE_STR STRING_FROM_IDENTIFIER(F_TARGET_ARCHITECTURE)
#define F_SYSTEM_STR STRING_FROM_IDENTIFIER(F_SYSTEM)

#define FACTOR_QNAME_STR STRING_FROM_IDENTIFIER(FACTOR_QNAME)
#define FACTOR_BASENAME_STR STRING_FROM_IDENTIFIER(FACTOR_BASENAME)
#define FACTOR_PACKAGE_STR STRING_FROM_IDENTIFIER(FACTOR_PACKAGE)
#define FACTOR_PATH(NAME) FACTOR_QNAME_STR "." NAME

#ifndef F_INTENTION
	#warning Compiler was not given an F_INTENTION preprocessor definition; presuming 'optimal'.
	#define F_INTENTION optimal
#endif

#define F_INTENTION_STR STRING_FROM_IDENTIFIER(F_INTENTION)

#define F_INTENTION_optimal 1
#define F_INTENTION_debug 2

#define F_INTENTION_coverage 8
#define F_INTENTION_profiling 4

/* Negatives used to identify non-functional/informative intents. */
#define F_INTENTION_delineation (-1)
#define F_INTENTION_analysis (-2)

#define _F_INTENTION_PREFIX() F_INTENTION_
#define _F_INTENTION_REF() F_INTENTION
#undef F_INTENTION_ID

/* 'F_INTENTION_' + F_INTENTION */
#define F_INTENTION_ID CONCAT_REFERENCES(_F_INTENTION_PREFIX(),_F_INTENTION_REF())

#define F_TRACE(y) 0

/* Switching macros used by applications. */
#define FV_OPTIMAL(y) (F_INTENTION_ID == F_INTENTION_optimal)
#define FV_DEBUG(y) (F_INTENTION_ID == F_INTENTION_debug)

/* Only coverage and debug */
#define FV_COVERAGE(y) (F_INTENTION_ID == F_INTENTION_coverage)
#define FV_PROFILING(y) (F_INTENTION_ID == F_INTENTION_profiling)

#define FV_DELINEATION(y) (F_INTENTION_ID == F_INTENTION_delineation)
#define FV_ANALYSIS(y) (F_INTENTION_ID == F_INTENTION_analysis)

#define FV_INJECTIONS(y) (FV_COVERAGE(y) || FV_DEBUG(y))
#endif /* guard */
