/**
	fault C Preprocessor interfaces and macros.
*/
#ifndef _FAULT_LIBC_H_
#define _FAULT_LIBC_H_

#define _CPP_QUOTE(x) #x
#define STRING_FROM_IDENTIFIER(X) _CPP_QUOTE(X)
#define CONCAT_IDENTIFIER(X, Y) X##Y
#define CONCAT_REFERENCES(X, Y) CONCAT_IDENTIFIER(X,Y)

#define PRODUCT_ARCHITECTURE_STR STRING_FROM_IDENTIFIER(PRODUCT_ARCHITECTURE)

#define MODULE_QNAME_STR STRING_FROM_IDENTIFIER(MODULE_QNAME)
#define MODULE_BASENAME_STR STRING_FROM_IDENTIFIER(MODULE_BASENAME)
#define MODULE_PACKAGE_STR STRING_FROM_IDENTIFIER(MODULE_PACKAGE)
#define MODULE_QPATH(NAME) MODULE_QNAME_STR "." NAME

#define FACTOR_QNAME_STR STRING_FROM_IDENTIFIER(FACTOR_QNAME)
#define FACTOR_BASENAME_STR STRING_FROM_IDENTIFIER(FACTOR_BASENAME)
#define FACTOR_PACKAGE_STR STRING_FROM_IDENTIFIER(FACTOR_PACKAGE)
#define FACTOR_PATH(NAME) FACTOR_QNAME_STR "." NAME

#ifndef F_PURPOSE
	#warning Compilation driver was not given a F_PURPOSE preprocessor definition
	#warning Presuming 'optimal' build.
	#define F_PURPOSE optimal
#endif

#define F_PURPOSE_STR STRING_FROM_IDENTIFIER(F_PURPOSE)

#define F_PURPOSE_optimal 1
#define F_PURPOSE_debug 2

#define F_PURPOSE_test 5
#define F_PURPOSE_metrics 10

#define F_PURPOSE_profiling 4
#define F_PURPOSE_coverage 9

#define _F_PURPOSE_PREFIX() F_PURPOSE_
#define _F_PURPOSE_REF() F_PURPOSE
#undef F_PURPOSE_ID
#define F_PURPOSE_ID CONCAT_REFERENCES(_F_PURPOSE_PREFIX(),_F_PURPOSE_REF())

#define F_TRACE(y) 0

#define FV_OPTIMAL(y) (F_PURPOSE_ID == F_PURPOSE_optimal)
#define FV_DEBUG(y) (F_PURPOSE_ID == F_PURPOSE_debug)

#define FV_TEST(y) (F_PURPOSE_ID == F_PURPOSE_test)
#define FV_METRICS(y) (F_PURPOSE_ID == F_PURPOSE_metrics)

#define FV_COVERAGE(y) (F_PURPOSE_ID == F_PURPOSE_coverage)
#define FV_PROFILING(y) (F_PURPOSE_ID == F_PURPOSE_profiling)

#endif
