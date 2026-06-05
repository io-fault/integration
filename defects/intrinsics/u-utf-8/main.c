#include <assert.h>
#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
#include <string.h>
#include <stdio.h>

#include <fault/utf-8.h>
#include <fault/libc.h>
#include <fault/test.h>

struct sample_utf_8 {
	uint32_t codepoint;
	const uint8_t *string;
};

const struct sample_utf_8 samples_1_bytes[] = {
	{0, "\x00"},
	{1, "\x01"},
	{0x7F, "\x7F"},
	{0xDCFF, "\xFF"},
	{0xDCF0, "\xF0"}
};
const struct sample_utf_8 samples_2_bytes[] = {
	{0x80, "\xC2\x80"},
	{0x81, "\xC2\x81"},
	{0x800-1, "\xDF\xBF"}
};
const struct sample_utf_8 samples_3_bytes[] = {
	{0x800, "\xE0\xA0\x80"},
	{0x801, "\xE0\xA0\x81"},
	{0x10000-1, "\xEF\xBF\xBF"}
};
const struct sample_utf_8 samples_4_bytes[] = {
	{0x10000, "\xF0\x90\x80\x80"},
	{0x10001, "\xF0\x90\x80\x81"},
	{0x1F4AB, "\xF0\x9F\x92\xAB"},
	{0x110000-1, "\xF4\x8F\xBF\xBF"}
};

/**
	// Check that the samples are encoded and decoded consistently.
*/
#define RECODE_TESTS(N) \
	Test(recode_##N##_byte_samples) \
	{ \
		const size_t n_samples = sizeof(samples_##N##_bytes) / sizeof(struct sample_utf_8); \
		struct sample_utf_8 *samples = samples_##N##_bytes; \
		\
		for (int i = 0; i < n_samples; ++i) \
		{ \
			uint32_t cp = 0xFFFFFFFF; \
			struct sample_utf_8 *su = &samples[i]; \
			uint8_t etxt[5]; \
			size_t used, ets; \
			ets = utf8_sequence_codepoint(etxt, su->codepoint); \
			etxt[ets] = 0; \
			used = utf8_identify_codepoint(&cp, etxt, ets); \
			test->equality(used, ets); \
			test->equality(cp, su->codepoint); \
			test->memcmp(etxt, su->string, ets); \
		} \
	}

	RECODE_TESTS(1)
	RECODE_TESTS(2)
	RECODE_TESTS(3)
	RECODE_TESTS(4)
#undef RECODE_TESTS

Test(recode_low)
{
	for (uint32_t i = 0; i < 0xDC00; ++i)
	{
		uint8_t etxt[5];
		uint32_t cp;
		size_t used, ets;

		ets = utf8_sequence_codepoint(etxt, i);
		etxt[ets] = 0;
		test->truth(ets > 0);

		used = utf8_identify_codepoint(&cp, etxt, ets);
		test->equality(used, ets);
		test->equality(cp, i);
	}
}

Test(recode_surrogate_escapes)
{
	for (uint32_t i = 0xDC00; i < 0xDD00; ++i)
	{
		uint8_t etxt[5];
		uint32_t cp;
		size_t used, ets;

		ets = utf8_sequence_codepoint(etxt, i);
		test->equality(ets, 1);
		test->equality(etxt[0], i - 0xDC00);

		used = utf8_identify_codepoint(&cp, etxt, ets);
		if (i <= 0xDC7F)
		{
			test->equality(used, ets);
			test->equality(cp, i - 0xDC00);
		}
		else
		{
			// The (length) limit used is forcing the escape here.
			test->equality(used, ets);
			test->equality(cp, i);
		}
	}
}

Test(recode_high)
{
	for (uint32_t i = 0xDD00; i < 0x110000; ++i)
	{
		uint8_t etxt[5];
		uint32_t cp;
		size_t used, ets;

		ets = utf8_sequence_codepoint(etxt, i);
		etxt[ets] = 0;
		test->truth(ets > 0);

		used = utf8_identify_codepoint(&cp, etxt, ets);
		test->equality(used, ets);
		test->equality(cp, i);
	}
}
