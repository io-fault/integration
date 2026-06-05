/**
	// Emit failure reports for integer comparisons of common sizes.
*/
#include <fault/libc.h>

#define TEST_SUITE_EXTENSION
#include <fault/test.h>

#define note_failed_exit() fprintf(stderr, "CRITICAL: test did not exit after contending absurdity\n")

Test(failed_comparison_format_i8)
{
	int8_t m = INT8_MIN;
	int8_t n = m - 1;

	test->equality(m, n);
	note_failed_exit();
}

Test(failed_comparison_format_i16)
{
	int16_t m = INT16_MIN;
	int16_t n = m - 1;

	test->equality(m, n);
	note_failed_exit();
}

Test(failed_comparison_format_i32)
{
	int32_t m = INT32_MIN;
	int32_t n = m - 1;

	test->equality(m, n);
	note_failed_exit();
}

Test(failed_comparison_format_i64)
{
	int64_t m = INT64_MIN;
	int64_t n = m - 1;

	test->equality(m, n);
	note_failed_exit();
}

Test(failed_comparison_format_u8)
{
	uint8_t m = 0xFF;
	uint8_t n = m + 1;

	test->equality(m, n);
	note_failed_exit();
}

Test(failed_comparison_format_u16)
{
	uint16_t m = 0xFFFF;
	uint16_t n = m + 1;

	test->equality(m, n);
	note_failed_exit();
}

Test(failed_comparison_format_u32)
{
	uint32_t m = 0xFFFFFFFF;
	uint32_t n = m + 1;

	test->equality(m, n);
	note_failed_exit();
}

Test(failed_comparison_format_u64)
{
	uint64_t m = 0xFFFFFFFFFFFFFFFF;
	uint64_t n = m + 1;

	test->equality(m, n);
	note_failed_exit();
}
