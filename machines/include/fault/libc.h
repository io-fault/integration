/**
	// fault C construction context environment support.
*/
#ifndef _FAULT_LIBC_H_
#define _FAULT_LIBC_H_

#ifdef __ALWAYS__
	#undef __ALWAYS__
	#warning __ALWAYS__ was defined.
#endif

#ifdef __NEVER__
	#undef __NEVER__
	#warning __NEVER__ was defined.
#endif

#define __ALWAYS__(...) 1
#define __NEVER__(...) 0

#ifdef __APPLE__
	#include <TargetConditionals.h>
#endif

#define _CPP_QUOTE(x) #x
#define STRING_FROM_IDENTIFIER(X) _CPP_QUOTE(X)
#define CONCAT_IDENTIFIER(X, Y) X##Y
#define CONCAT_REFERENCES(X, Y) CONCAT_IDENTIFIER(X,Y)

#define FV_ARCHITECTURE_STR STRING_FROM_IDENTIFIER(FV_ARCHITECTURE)
#define FV_SYSTEM_STR STRING_FROM_IDENTIFIER(FV_SYSTEM)

#define F_PROJECT_STR STRING_FROM_IDENTIFIER(F_PROJECT)
#define F_FACTOR_STR STRING_FROM_IDENTIFIER(F_FACTOR)

#ifdef F_CONTEXT
	#define F_CONTEXT_STR STRING_FROM_IDENTIFIER(F_CONTEXT)
	#define F_PROJECT_PATH_STR F_CONTEXT_STR "." F_PROJECT_STR
	#define FACTOR_CONTEXT(S, P) F_CONTEXT_STR S P
#else
	#define F_PROJECT_PATH_STR F_PROJECT_STR
	#define FACTOR_CONTEXT(S, P) P
#endif

#define FACTOR_PATH_STR F_PROJECT_PATH_STR "." F_FACTOR_STR
#define FACTOR_PATH(NAME) FACTOR_PATH_STR "." NAME

#ifndef FV_INTENTION
	#warning Compiler was not given an FV_INTENTION preprocessor definition; presuming 'optimal'.
	#define FV_INTENTION optimal
#endif

#define FV_INTENTION_STR STRING_FROM_IDENTIFIER(FV_INTENTION)

#define FV_INTENTION_optimal 1
#define FV_INTENTION_debug 2

#define FV_INTENTION_coverage 8
#define FV_INTENTION_profiling 4

/* Negatives used to identify non-functional/informative intents. */
#define FV_INTENTION_delineation (-1)
#define FV_INTENTION_analysis (-2)

#define _FV_INTENTION_PREFIX() FV_INTENTION_
#define _FV_INTENTION_REF() FV_INTENTION
#undef FV_INTENTION_ID

/* 'FV_INTENTION_' + FV_INTENTION */
#define FV_INTENTION_ID CONCAT_REFERENCES(_FV_INTENTION_PREFIX(),_FV_INTENTION_REF())

#define F_TRACE(y) 0

/* Switching macros used by applications. */
#define FV_OPTIMAL(y) (FV_INTENTION_ID == FV_INTENTION_optimal)
#define FV_DEBUG(y) (FV_INTENTION_ID == FV_INTENTION_debug)

/* Only coverage and debug */
#define FV_COVERAGE(y) (FV_INTENTION_ID == FV_INTENTION_coverage)
#define FV_PROFILING(y) (FV_INTENTION_ID == FV_INTENTION_profiling)

#define FV_DELINEATION(y) (FV_INTENTION_ID == FV_INTENTION_delineation)
#define FV_ANALYSIS(y) (FV_INTENTION_ID == FV_INTENTION_analysis)

#define FV_INJECTIONS(y) (FV_COVERAGE(y) || FV_DEBUG(y))
#endif /* guard */
