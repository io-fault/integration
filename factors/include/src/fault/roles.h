/*
 * Symbol for filting coverage results.
 */
#define XCOVERAGE
#define _CPP_QUOTE(x) #x
#define STRING_FROM_IDENTIFIER(X) _CPP_QUOTE(X)
#define CONCAT_IDENTIFIER(X, Y) X##Y

#define MODULE_QNAME_STR STRING_FROM_IDENTIFIER(MODULE_QNAME)
#define MODULE_BASENAME_STR STRING_FROM_IDENTIFIER(MODULE_BASENAME)
#define MODULE_PACKAGE_STR STRING_FROM_IDENTIFIER(MODULE_PACKAGE)
#define QPATH(NAME) MODULE_QNAME_STR "." NAME

#define F_ROLE_TEST_ID 5
#define F_ROLE_SURVEY_ID 10
#define F_ROLE_FACTOR_ID 1
#define F_ROLE_INSPECT_ID -1
#define F_ROLE_DEBUG_ID 2

#define TEST(y) (F_ROLE_ID == F_ROLE_TEST_ID || F_ROLE_ID == F_ROLE_SURVEY_ID)
#define DEBUG(y) (F_ROLE_ID == F_ROLE_DEBUG_ID)
#define FACTOR(y) (F_ROLE_ID == F_ROLE_FACTOR_ID)
#define INSPECT(y) (F_ROLE_ID == F_ROLE_INSPECT_ID)
#define SURVEY(y) (F_ROLE_ID == F_ROLE_SURVEY_ID)

#ifndef F_ROLE_ID
	#error compilation driver was not given a F_ROLE_ID preprocessor definition
#endif
