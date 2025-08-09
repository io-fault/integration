/**
	// Validate that the proxies are compensating for the invasive macros.
*/
#include <fault/libc.h>

#define TEST_SUITE_EXTENSION
#include <fault/test.h>

static int
pstrcmp(void)
{
	// Out of (test) context call.
	return(strcmp("a", "b") != 0);
}

Test(direct_strcmp)
{
	test->truth(pstrcmp());

	// In test context, but not test->qualified.
	test->truth(strcmp("a", "b"));
	test->truth(!strcmp("a", "a"));
}

static int
pstrcasecmp(void)
{
	// Out of (test) context call.
	return(strcasecmp("a", "b") != 0);
}

Test(direct_strcasecmp)
{
	test->truth(pstrcasecmp());

	// In test context, but not test->qualified.
	test->truth(strcasecmp("a", "b"));
	test->truth(!strcasecmp("a", "A"));
	test->truth(!strcasecmp("a", "a"));
}

static int
pwcscasecmp(void)
{
	return(wcscasecmp(L"a", L"b") != 0);
}

Test(direct_wcscasecmp)
{
	test->truth(pwcscasecmp());

	// In test context, but not test->qualified.
	test->truth(wcscasecmp(L"a", L"b"));
	test->truth(!wcscasecmp(L"a", L"A"));
	test->truth(!wcscasecmp(L"a", L"a"));
}

static int
pwcscmp(void)
{
	return(wcscmp(L"a", L"b") != 0);
}

Test(direct_wcscmp)
{
	test->truth(pwcscmp());

	// In test context, but not test->qualified.
	test->truth(wcscmp(L"a", L"b"));
	test->truth(wcscmp(L"a", L"A"));
	test->truth(!wcscmp(L"a", L"a"));
}

static int
pmemcmp(void)
{
	// Out of (test) context call.
	return(memcmp("a", "b", 1) != 0);
}

Test(direct_memcmp)
{
	test->truth(pmemcmp());

	// In test context, but not test->qualified.
	test->truth(memcmp("a", "b", 1));
	test->truth(!memcmp("a", "a", 1));
}

static int
pmemchr(void)
{
	// Out of (test) context call.
	return(memchr("a", 'a', 1) != NULL);
}

Test(direct_memchr)
{
	test->truth(pmemchr());

	// In test context, but not test->qualified.
	test->truth(memchr("a", 'a', 1) != NULL);
	test->truth(memchr("a", 'b', 1) == NULL);
}

static int
pmemrchr(void)
{
	return(memrchr("a", 'a', 1) != NULL);
}

Test(direct_memrchr)
{
	test->truth(pmemrchr());

	// In test context, but not test->qualified.
	test->truth(memrchr("a", 'a', 1) != NULL);
	test->truth(memrchr("a", 'b', 1) == NULL);
}
