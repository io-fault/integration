#include <assert.h>
#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
#include <string.h>
#include <stdio.h>

#include <fault/utf-8.h>
#include <fault/libc.h>

#define TEST_SUITE_EXTENSION
#include <fault/test.h>

/**
	// Validate range checks of utf8_error.

	// UTF-8 requires that codepoint values are sequenced using the minimum
	// number of bytes. For instance, the `NUL` character should not be encoded
	// using anything other than a single byte. However, zero, `NUL`, could be
	// stored in a two, three, or four byte sequence.
*/
Test(utf8_errors_range)
{
	uint8_t cv[5] = {0,};
	size_t cd, limit = sizeof(cv);
	uint32_t cp = 0;
	utf8_error_t error;

	// Use the internal sequence functions to circumvent the switch
	// and force illegal values.

	utf8_sequence_codepoint_2(cv, 0x7F);
	cd = utf8_identify_codepoint(&cp, cv, 2);
	error = utf8_error(cv, 2, cd, cp);
	test->equality(error.errcode, utf8_error_value_out_of_range);

	utf8_sequence_codepoint_3(cv, 0x7FF);
	cd = utf8_identify_codepoint(&cp, cv, 3);
	error = utf8_error(cv, 3, cd, cp);
	test->equality(error.errcode, utf8_error_value_out_of_range);

	utf8_sequence_codepoint_4(cv, 0xFFFF);
	cd = utf8_identify_codepoint(&cp, cv, 4);
	error = utf8_error(cv, 4, cd, cp);
	test->equality(error.errcode, utf8_error_value_out_of_range);
}

/**
	// Validate missing continuations errors and that the index is reported.
*/
Test(utf8_errors_missing_continuation)
{
	uint8_t cv[5] = {0,};
	size_t cd, limit = sizeof(cv);
	uint32_t cp = 0;
	utf8_error_t error;

	for (int i = 0; i < 3; ++i)
	{
		test->equality(4, utf8_sequence_codepoint(cv, 0x110000-1));

		// Overwrite a continuation; only the first one is reported.
		cv[i+1] = i+1;

		cd = utf8_identify_codepoint(&cp, cv, 4);
		error = utf8_error(cv, 5, cd, cp);
		test->equality(utf8_error_missing_continuation, error.errcode);
		test->equality(i+1, error.errindex);
	}
}

/**
	// Validate the surrogate range checks of utf8_error.
*/
Test(utf8_errors_surrogate_value)
{
	// Avoid 0xDC00 as it gets restored.
	static uint32_t samples[] = {0xD800, 0xDE00, 0xDFFF};
	uint8_t cv[5] = {0,};
	size_t cd, limit = sizeof(cv);
	uint32_t cp = 0;
	utf8_error_t error;

	for (int i = 0; i < sizeof(samples) / sizeof(uint32_t); ++i)
	{
		test->equality(3, utf8_sequence_codepoint(cv, samples[i]));
		cd = utf8_identify_codepoint(&cp, cv, 4);
		error = utf8_error(cv, 5, cd, cp);
		test->equality(utf8_error_surrogate_character, error.errcode);
	}
}

/**
	// Validate insufficient data errors.
*/
Test(utf8_errors_insufficient_data)
{
	uint8_t cv[5] = {0,};
	size_t cd, limit = sizeof(cv);
	uint32_t cp = 0;
	utf8_error_t error;

	test->equality(2, utf8_sequence_codepoint(cv, 0x81));
	cd = utf8_identify_codepoint(&cp, cv, 1);
	error = utf8_error(cv, 1, cd, cp);
	test->equality(utf8_error_insufficient_data, error.errcode);
	test->equality(1, error.errindex);

	for (int i = 1; i < 3; ++i)
	{
		test->equality(3, utf8_sequence_codepoint(cv, 0x801));
		cd = utf8_identify_codepoint(&cp, cv, i);
		error = utf8_error(cv, i, cd, cp);
		test->equality(utf8_error_insufficient_data, error.errcode);
		test->equality(3 - i, error.errindex);
	}

	for (int i = 1; i < 4; ++i)
	{
		test->equality(4, utf8_sequence_codepoint(cv, 0x10001));
		cd = utf8_identify_codepoint(&cp, cv, i);
		error = utf8_error(cv, i, cd, cp);
		test->equality(utf8_error_insufficient_data, error.errcode);
		test->equality(4 - i, error.errindex);
	}
}

/**
	// Validate invalidate sequence errors.
*/
Test(utf8_errors_invalid_sequence_length)
{
	uint8_t cv[5] = {0xFF, UTF8_CONTINUATION, 0,};
	size_t cd, limit = sizeof(cv);
	uint32_t cp = 0;
	utf8_error_t error;

	cd = utf8_identify_codepoint(&cp, cv, 2);
	error = utf8_error(cv, 2, cd, cp);
	test->equality(utf8_error_invalid_sequence_length, error.errcode);
}

/**
	// Validate out of sequence continuation errors.
*/
Test(utf8_errors_unexpected_continuation)
{
	uint8_t cv[5] = {0, 0,};
	size_t cd, limit = sizeof(cv);
	uint32_t cp = 0;
	utf8_error_t error;

	for (int i = 0; i <= (0xFF >> 2); ++i)
	{
		cv[0] = UTF8_CONTINUATION | i;
		cd = utf8_identify_codepoint(&cp, cv, limit);
		error = utf8_error(cv, limit, cd, cp);
		test->equality(utf8_error_unexpected_continuation, error.errcode);
	}
}

/**
	// Validate the functions providing access to error identifiers and descriptions.
*/
Test(utf8_errors_information_tables)
{
	enum UTF8Error uec = utf8_error_none;

	test->truth(!utf8_error_identifier(uec));
	test->truth(!utf8_error_message(uec));

	for (++uec; uec < utf8_error_sentinal; ++uec)
	{
		test->truth((int) utf8_error_identifier(uec));
		test->truth((int) utf8_error_message(uec));
	}
}
