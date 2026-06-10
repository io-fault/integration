/**
	// Validate that the proxies are compensating for the invasive macros.
*/
#include <fault/libc.h>

#define TEST_SUITE_EXTENSION
#include <fault/test.h>

#define note_failed_exit() fprintf(stderr, "CRITICAL: test did not exit after contending absurdity\n")

Test(failed_size_t_size_report)
{
	test->equality(0, sizeof(size_t));
	note_failed_exit();
}

Test(failed_short_size_report)
{
	test->equality(0, sizeof(short));
	note_failed_exit();
}

Test(failed_int_size_report)
{
	test->equality(0, sizeof(int));
	note_failed_exit();
}

Test(failed_maxint_size_report)
{
	test->equality(0, sizeof(intmax_t));
	note_failed_exit();
}
