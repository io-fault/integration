/**
	// Exercise trace modifier.
*/
#include <fault/libc.h>

#define TEST_SUITE_EXTENSION
#include <fault/test.h>

Test(trace)
{
	test(~)->truth(true);
	test(~)->truth(!false);
}

Test(trace_inversion)
{
	test(~);
	test(!)->strcmp("a", "b");
	test(!~)->equality(0, 100);
}

Test(trace_never_fail)
{
	test(~);
	test(+)->strcmp("a", "b");
	test(+~)->strcmp("a", "a");
}
