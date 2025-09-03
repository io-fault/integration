/**
	// Evaluation of fault/test.h test control failures.
*/
#include <fault/libc.h>

#include <fault/test.h>

#define note_failed_exit() fprintf(stderr, "CRITICAL: test did not exit after contending absurdity\n")

Test(skipped)
{
	test->skip("formatted messaged: %s", "skip");
	note_failed_exit();
}

Test(fail)
{
	test->fail("explicit failure %s", "message");
	note_failed_exit();
}

Test(failed_strcmpf)
{
	test->strcmpf("test 10 'sub' string", "test %d '%s' string", -1, "sub");
	note_failed_exit();
}

Test(failed_truth)
{
	test->truth(0 > 0);
	note_failed_exit();
}

Test(failed_memcmp)
{
	test->memcmp("former", "forter", 6);
	note_failed_exit();
}

Test(failed_memchr)
{
	test->memchr("former", 'z', 6);
	note_failed_exit();
}

Test(failed_memrchr)
{
	test->memrchr("former", 'z', 6);
	note_failed_exit();
}

Test(failed_strcmp)
{
	test->strcmp("a", "b");
	note_failed_exit();
}

Test(failed_strcasecmp)
{
	test->strcasecmp("a", "b");
	note_failed_exit();
}

Test(failed_wcscmp)
{
	test->wcscmp(L"a", L"b");
	note_failed_exit();
}

Test(failed_wcscasecmp)
{
	test->wcscasecmp(L"a", L"b");
	note_failed_exit();
}

Test(failed_wcsstr)
{
	test->wcsstr(L"haystack of nothing", L"needle");
	note_failed_exit();
}

Test(failed_strstr)
{
	test->strstr("haystack of nothing", "needle");
	note_failed_exit();
}

Test(failed_strcasestr)
{
	test->strcasestr("haystack of nothing", "needle");
	note_failed_exit();
}

Test(failed_equality)
{
	test->equality(0, 1);
	note_failed_exit();
}
