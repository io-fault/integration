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

#endif /* guard */
