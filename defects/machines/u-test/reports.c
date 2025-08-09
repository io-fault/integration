/**
	// Validate that the proxies are compensating for the invasive macros.
*/
#include <fault/libc.h>

#define TEST_SUITE_EXTENSION
#include <fault/test.h>

Test(failed_size_t_size_report)
{
	test->equality(0, sizeof(size_t));
}

Test(failed_short_size_report)
{
	test->equality(0, sizeof(short));
}

Test(failed_int_size_report)
{
	test->equality(0, sizeof(int));
}

Test(failed_maxint_size_report)
{
	test->equality(0, sizeof(intmax_t));
}
