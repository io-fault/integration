/**
	// Exercise tests primarily validating the absence of (memory) violations.

	// Only input samples are tested as output consistency is not desired across
	// implementation changes.
*/
#include <stdint.h>
#include <unistd.h>
#include <time.h>
#include <fault/libc.h>
#include <fault/metrics.h>
#include <fault/test.h>

#include <fault/hash.h>

struct Sample {
	const size_t length;
	const char *const data;
};
#define R(s) {sizeof(s)-1, s},

const struct Sample samples[] = {
	R("")
	R("0")
	R("01")
	R("012")
	R("01234")
	R("012345")
	R("0123456")
	R("01234567")
	R("012345678")
	R("0123456789")
	R("0123456789A")
	R("0123456789AB")
	R("0123456789ABC")
	R("0123456789ABCD")
	R("0123456789ABCDE")
	R("0123456789ABCDEF"
	"0123456789ABCDEF")
	R("0123456789ABCDEF"
	"0123456789ABCDEF"
	"0123456789ABCDEF"
	"0123456789ABCDEF")
	R("\x00")
	R("\x00\x00")
	R("\x00\x00\x00\x00")
	R("\x00\x00\x00\x00"
	"\x00\x00\x00\x00")
	R("\x00\x00\x00\x00"
	"\x00\x00\x00\x00"
	"\x00\x00\x00\x00"
	"\x00\x00\x00\x00")

	R("\x00\x00\x00\x00"
	"\x00\x00\x00\x00"
	"\x00\x00\x00\x00"
	"\x00\x00\x00\x00"
	"\x00\x00\x00\x00"
	"\x00\x00\x00\x00"
	"\x00\x00\x00\x00"
	"\x00\x00\x00\x00"
	"\x00\x00\x00\x00"
	"\x00\x00\x00\x00"
	"\x00\x00\x00\x00"
	"\x00\x00\x00\x00")
};

/**
	// Aligned and complete 64-bit hash.
*/
Test(h64_aligned_difference)
{
	int i;
	for (i=0; i < sizeof(samples) / sizeof(samples[0]); ++i)
	{
		size_t sl = samples[i].length;
		void *data = samples[i].data;
		uint64_t h;
		h = hash_64(0, data, sl);

		if (sl % sizeof(h) == 0)
			test->equality(hash_aligned_64(0, data, sl), h);
		else
			test(!)->equality(hash_aligned_64(0, data, sl), h);
	}
}

/**
	// Aligned and complete 32-bit hash.
*/
Test(h32_aligned_difference)
{
	for (int i=0; i < sizeof(samples) / sizeof(samples[0]); ++i)
	{
		size_t sl = samples[i].length;
		void *data = samples[i].data;
		uint32_t h;
		h = hash_32(0, data, sl);

		if (sl % sizeof(h) == 0)
			test->equality(hash_aligned_32(0, data, sl), h);
		else
			test(!)->equality(hash_aligned_32(0, data, sl), h);
	}
}

/**
	// Aligned and complete 16-bit hash.
*/
Test(h16_aligned_difference)
{
	for (int i=0; i < sizeof(samples) / sizeof(samples[0]); ++i)
	{
		size_t sl = samples[i].length;
		void *data = samples[i].data;
		uint16_t h;
		h = hash_16(0, data, sl);

		if (sl % sizeof(h) == 0)
			test->equality(hash_aligned_16(0, data, sl), h);
		else
			test(!)->equality(hash_aligned_16(0, data, sl), h);
	}
}

/**
	// Byte hash should always be aligned.
*/
Test(h8_aligned_difference)
{
	for (int i=0; i < sizeof(samples) / sizeof(samples[0]); ++i)
	{
		size_t sl = samples[i].length;
		void *data = samples[i].data;
		uint8_t h;
		h = hash_8(0, data, sl);

		if (sl % sizeof(h) == 0)
			test->equality(hash_aligned_8(0, data, sl), h);
		else
			test->fail("uint8_t is expected to be 1-byte");
	}
}
