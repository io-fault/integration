/**
	// Evaluation of fault/test.h test controls.
*/
#include <fault/libc.h>

#include <fault/test.h>

#define note_failed_exit() fprintf(stderr, "CRITICAL: test did not exit after contending absurdity\n")

Test(test)
{
	test(true);
	test(!false);
	test(1);
	test(!0);
	test(0 == 0);
	test(1 != 0);
	test(1 > 0);
	test(0 < 1);
	test(1 <= 1);
	test(1 >= 1);
}

Test(strcmpf)
{
	test->strcmpf("test 10 'sub' string", "test %d '%s' string", 10, "sub");
}

Test(truth)
{
	test->truth(0 == 0);
	contend_truth(1 == 1);
}

Test(equality)
{
	test->equality(0, 0);
	contend_equality(0, 0);
}

Test(memcmp)
{
	test->memcmp("prefix", "pre", 3);
	contend_memcmp("prefix", "pre", 3);
	test->truth(memcmp("prefix", "pre", 3) == 0);
}

Test(memchr)
{
	test->memchr("prefix", 'f', 6);
	contend_memchr("prefix", 'e', 6);
	test->truth(memchr("prefix", 'z', 6) == NULL);
}

Test(memrchr)
{
	test->memrchr("prefix", 'p', 6);
	contend_memrchr("prefix", 'p', 6);
	test->truth(memrchr("prefix", 'z', 6) == NULL);
}

Test(strcmp)
{
	test->strcmp("passed", "passed");
	contend_strcmp("passed", "passed");
}

Test(strcasecmp)
{
	test->strcasecmp("Passed", "pasSed");
	contend_strcasecmp("Passed", "pasSed");
	test->truth(strcasecmp("Passed", "paSsed") == 0);
}

Test(strstr)
{
	test->strstr("haystack of needles", "needle");
}

Test(strcasestr)
{
	test->strcasestr("haystack of nEEdles", "needle");
}

Test(wcscmp)
{
	test->wcscmp(L"passed", L"passed");
	contend_wcscmp(L"passed", L"passed");
}

Test(wcscasecmp)
{
	test->wcscasecmp(L"Passed", L"pasSed");
	contend_wcscasecmp(L"Passed", L"pasSed");
	test->truth(wcscasecmp(L"Passed", L"paSsed") == 0);
}

Test(wcsstr)
{
	test->wcsstr(L"haystack of needles", L"needle");
}
