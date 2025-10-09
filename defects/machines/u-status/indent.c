/**
	// Validate stf_indent_text.
*/
#include <fault/libc.h>

#define TEST_SUITE_EXTENSION
#include <fault/test.h>
#include <fault/status.h>

#define SZB(NAME, DATA) struct iovec NAME = {(char *) DATA, sizeof(DATA)}

static inline int
_memcnt(char *buf, size_t len, int c)
{
	char *p = buf;
	size_t r = len, count = 0;

	while (p = memchr(p, c, r))
	{
		r = len - ((intptr_t) p - (intptr_t) buf);

		// Count while tracking remaining length.
		while (r > 0 && *p == c)
		{
			++count;
			++p;
			--r;
		}
	}

	return(count);
}

Test(indent_one_line)
{
	SZB(line, "Single line of text, no end.");
	uint8_t *buf;
	size_t buflen;

	buflen = stf_indent_text(&buf, line.iov_base, line.iov_len, 0, 1);
	test->equality(line.iov_len + 1, buflen);
	test->memcmp("\tSingle line of text, no end.", buf, buflen);

	STF_FREE(buf);
}

Test(indent_two_lines)
{
	SZB(line, "First line of text, with end.\nSecond line; no end.");
	uint8_t *buf;
	size_t buflen;

	buflen = stf_indent_text(&buf, line.iov_base, line.iov_len, 0, 1);
	test->equality(line.iov_len + 2, buflen);
	test->memcmp("\tFirst line of text, with end.\n\tSecond line; no end.", buf, buflen);

	STF_FREE(buf);
}

Test(indent_three_lines)
{
	SZB(line, "First line of text, with end.\nSecond line; with end.\n");
	uint8_t *buf;
	size_t buflen;

	buflen = stf_indent_text(&buf, line.iov_base, line.iov_len, 0, 1);
	test->equality(line.iov_len + 3, buflen);
	test->memcmp("\tFirst line of text, with end.\n\tSecond line; with end.\n\t", buf, buflen);

	STF_FREE(buf);
}

Test(indent_only_lines)
{
	SZB(line, "\n\n\n");
	uint8_t *buf;
	size_t buflen;

	for (int i = 0; i < 12; ++i)
	{
		buflen = stf_indent_text(&buf, line.iov_base, line.iov_len, 0, i);
		test->equality(line.iov_len + i, buflen);
		test->memcmp("\n\n\n", buf, 3);
		test->equality(i, _memcnt(buf, buflen, '\t'));

		STF_FREE(buf);
		buf = NULL;
	}
}

/**
	// NUL characters are not treated specially, so insertions are performed.
*/
Test(indent_nul_line)
{
	SZB(line, "");
	uint8_t *buf;
	size_t buflen;

	for (int i = 0; i < 5; ++i)
	{
		buflen = stf_indent_text(&buf, line.iov_base, line.iov_len, 0, i);
		test->equality(line.iov_len + i, buflen);
		test->equality(i, _memcnt(buf, buflen, '\t'));

		STF_FREE(buf);
		buf = NULL;
	}
}

/**
	// Zero length.
*/
Test(indent_empty_line)
{
	struct iovec line = {"", 0};
	uint8_t *buf;
	size_t buflen;

	for (int i = 0; i < 5; ++i)
	{
		buflen = stf_indent_text(&buf, line.iov_base, line.iov_len, 0, i);
		test->equality(0, buflen);
		test->equality(0, _memcnt(buf, buflen, '\t'));

		STF_FREE(buf);
		buf = NULL;
	}
}
