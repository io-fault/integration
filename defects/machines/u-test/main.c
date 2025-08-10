/**
	// Evaluation of fault/test.h test controls.
*/
#include <fault/libc.h>

#include <fault/test.h>

#define note_failed_exit() fprintf(stderr, "CRITICAL: test did not exit after contending absurdity\n")

Test(passed_test)
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

Test(failed_test_zero)
{
	test(!1);
}

Test(failed_test_bool)
{
	test(false);
}

Test(explicit_failure)
{
	test->fail("explicit failure %s message", "'substituted'");
	note_failed_exit();
}

Test(skipped)
{
	test->skip("not applicable to platform: %s", "zag");
	note_failed_exit();
}

Test(passed_strcmpf)
{
	test->strcmpf("test 10 'sub' string", "test %d '%s' string", 10, "sub");
}

Test(failed_strcmpf)
{
	test->strcmpf("test 10 'sub' string", "test %d '%s' string", -1, "sub");
}

Test(passed_truth)
{
	test->truth(0 == 0);
	contend_truth(1 == 1);
}

Test(failed_truth)
{
	test->truth(0 > 0);
	note_failed_exit();
}

Test(passed_memcmp)
{
	test->memcmp("prefix", "pre", 3);
	contend_memcmp("prefix", "pre", 3);
	test->truth(memcmp("prefix", "pre", 3) == 0);
}

Test(failed_memcmp)
{
	test->memcmp("former", "forter", 6);
	note_failed_exit();
}

Test(passed_memchr)
{
	test->memchr("prefix", 'f', 6);
	contend_memchr("prefix", 'e', 6);
	test->truth(memchr("prefix", 'z', 6) == NULL);
}

Test(failed_memchr)
{
	test->memchr("former", 'z', 6);
	note_failed_exit();
}

Test(passed_strcmp)
{
	test->strcmp("passed", "passed");
	contend_strcmp("passed", "passed");
}

Test(failed_strcmp)
{
	test->strcmp("a", "b");
	note_failed_exit();
}

Test(passed_strcasecmp)
{
	test->strcasecmp("Passed", "pasSed");
	contend_strcasecmp("Passed", "pasSed");
	test->truth(strcasecmp("Passed", "paSsed") == 0);
}

Test(failed_strcasecmp)
{
	test->strcasecmp("a", "b");
	note_failed_exit();
}

Test(passed_wcscmp)
{
	test->wcscmp(L"passed", L"passed");
	contend_wcscmp(L"passed", L"passed");
}

Test(failed_wcscmp)
{
	test->wcscmp(L"a", L"b");
	note_failed_exit();
}

Test(passed_wcscasecmp)
{
	test->wcscasecmp(L"Passed", L"pasSed");
	contend_wcscasecmp(L"Passed", L"pasSed");
	test->truth(wcscasecmp(L"Passed", L"paSsed") == 0);
}

Test(failed_wcscasecmp)
{
	test->wcscasecmp(L"a", L"b");
	note_failed_exit();
}

Test(passed_wcsstr)
{
	test->wcsstr(L"haystack of needles", L"needle");
}

Test(failed_wcsstr)
{
	test->wcsstr(L"haystack of nothing", L"needle");
}

Test(passed_strstr)
{
	test->strstr("haystack of needles", "needle");
}

Test(failed_strstr)
{
	test->strstr("haystack of nothing", "needle");
}

Test(passed_strcasestr)
{
	test->strcasestr("haystack of nEEdles", "needle");
}

Test(failed_strcasestr)
{
	test->strcasestr("haystack of nothing", "needle");
}

Test(passed_inequality)
{
	test->inequality(1, 0);
	contend_inequality(1, 0);
}

Test(failed_inequality)
{
	test->inequality(0, 0);
	note_failed_exit();
}

Test(passed_equality)
{
	test->equality(0, 0);
	contend_equality(0, 0);
}

Test(failed_equality)
{
	test->equality(0, 1);
	note_failed_exit();
}
