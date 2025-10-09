/**
	// Validate fault/base-64.h encoding and decoding.
*/
#include <fault/libc.h>
#include <fault/test.h>
#include <fault/base-64.h>

#define sized(S) sizeof(S) - 1, S

typedef struct {
	size_t str_length;
	const char *str_content;
} sstr_t;

static const sstr_t strings[] = {
	{sized(base64_digit_index)},
	{sized("\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x10")},
	{sized("\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x10")},
};

typedef struct {
	size_t dlength;
	const char *decoded;

	size_t elength;
	const char *encoded;
} sstrpair_t;

static const sstrpair_t samples[] = {
	{sized(""), sized("")},
	{sized("\0"), sized("AA==")},
	{sized("\0\0"), sized("AAA=")},
	{sized("\0\0\0"), sized("AAAA")},
	{sized("\xFF"), sized("/w==")},
	{sized("\xFF\xFF"), sized("//8=")},
	{sized("\xFF\xFF\xFF"), sized("////")},
	{sized("\c"), sized("Yw==")},
	{sized(" "), sized("IA==")},
	{sized("\n"), sized("Cg==")},
	{sized("sample\n"), sized("c2FtcGxlCg==")},

	// Misaligned.
	{sized("\c"), sized("Yw")},
	{sized("\0"), sized("AA")},
	{sized("\0\0"), sized("AAA")},
	{sized("\n"), sized("Cg")},
	{sized("\xFF"), sized("/w")},
	{sized("\xFF\xFF"), sized("//8")},

	// Strictly, error cases.
	// Missing digits presumed zero.
	{sized("\0"), sized("A")},
	{sized("\x04"), sized("B")},

	// 0-256
	{
		sized(
			"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b"
			"\x0c\x0d\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17"
			"\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f\x20\x21\x22\x23"
			"\x24\x25\x26\x27\x28\x29\x2a\x2b\x2c\x2d\x2e\x2f"
			"\x30\x31\x32\x33\x34\x35\x36\x37\x38\x39\x3a\x3b"
			"\x3c\x3d\x3e\x3f\x40\x41\x42\x43\x44\x45\x46\x47"
			"\x48\x49\x4a\x4b\x4c\x4d\x4e\x4f\x50\x51\x52\x53"
			"\x54\x55\x56\x57\x58\x59\x5a\x5b\x5c\x5d\x5e\x5f"
			"\x60\x61\x62\x63\x64\x65\x66\x67\x68\x69\x6a\x6b"
			"\x6c\x6d\x6e\x6f\x70\x71\x72\x73\x74\x75\x76\x77"
			"\x78\x79\x7a\x7b\x7c\x7d\x7e\x7f\x80\x81\x82\x83"
			"\x84\x85\x86\x87\x88\x89\x8a\x8b\x8c\x8d\x8e\x8f"
			"\x90\x91\x92\x93\x94\x95\x96\x97\x98\x99\x9a\x9b"
			"\x9c\x9d\x9e\x9f\xa0\xa1\xa2\xa3\xa4\xa5\xa6\xa7"
			"\xa8\xa9\xaa\xab\xac\xad\xae\xaf\xb0\xb1\xb2\xb3"
			"\xb4\xb5\xb6\xb7\xb8\xb9\xba\xbb\xbc\xbd\xbe\xbf"
			"\xc0\xc1\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xcb"
			"\xcc\xcd\xce\xcf\xd0\xd1\xd2\xd3\xd4\xd5\xd6\xd7"
			"\xd8\xd9\xda\xdb\xdc\xdd\xde\xdf\xe0\xe1\xe2\xe3"
			"\xe4\xe5\xe6\xe7\xe8\xe9\xea\xeb\xec\xed\xee\xef"
			"\xf0\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xfb"
			"\xfc\xfd\xfe\xff"
		),
		sized(
			"AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8gISIjJCUmJygpKissLS4vMDEyMzQ1Njc4"
			"OTo7PD0+P0BBQkNERUZHSElKS0xNTk9QUVJTVFVWV1hZWltcXV5fYGFiY2RlZmdoaWprbG1ub3Bx"
			"cnN0dXZ3eHl6e3x9fn+AgYKDhIWGh4iJiouMjY6PkJGSk5SVlpeYmZqbnJ2en6ChoqOkpaanqKmq"
			"q6ytrq+wsbKztLW2t7i5uru8vb6/wMHCw8TFxsfIycrLzM3Oz9DR0tPU1dbX2Nna29zd3t/g4eLj"
			"5OXm5+jp6uvs7e7v8PHy8/T19vf4+fr7/P3+/w=="
		)
	},

	// 256-0
	{
		sized(
			"\xff\xfe\xfd\xfc\xfb\xfa\xf9\xf8\xf7\xf6\xf5\xf4"
			"\xf3\xf2\xf1\xf0\xef\xee\xed\xec\xeb\xea\xe9\xe8"
			"\xe7\xe6\xe5\xe4\xe3\xe2\xe1\xe0\xdf\xde\xdd\xdc"
			"\xdb\xda\xd9\xd8\xd7\xd6\xd5\xd4\xd3\xd2\xd1\xd0"
			"\xcf\xce\xcd\xcc\xcb\xca\xc9\xc8\xc7\xc6\xc5\xc4"
			"\xc3\xc2\xc1\xc0\xbf\xbe\xbd\xbc\xbb\xba\xb9\xb8"
			"\xb7\xb6\xb5\xb4\xb3\xb2\xb1\xb0\xaf\xae\xad\xac"
			"\xab\xaa\xa9\xa8\xa7\xa6\xa5\xa4\xa3\xa2\xa1\xa0"
			"\x9f\x9e\x9d\x9c\x9b\x9a\x99\x98\x97\x96\x95\x94"
			"\x93\x92\x91\x90\x8f\x8e\x8d\x8c\x8b\x8a\x89\x88"
			"\x87\x86\x85\x84\x83\x82\x81\x80\x7f\x7e\x7d\x7c"
			"\x7b\x7a\x79\x78\x77\x76\x75\x74\x73\x72\x71\x70"
			"\x6f\x6e\x6d\x6c\x6b\x6a\x69\x68\x67\x66\x65\x64"
			"\x63\x62\x61\x60\x5f\x5e\x5d\x5c\x5b\x5a\x59\x58"
			"\x57\x56\x55\x54\x53\x52\x51\x50\x4f\x4e\x4d\x4c"
			"\x4b\x4a\x49\x48\x47\x46\x45\x44\x43\x42\x41\x40"
			"\x3f\x3e\x3d\x3c\x3b\x3a\x39\x38\x37\x36\x35\x34"
			"\x33\x32\x31\x30\x2f\x2e\x2d\x2c\x2b\x2a\x29\x28"
			"\x27\x26\x25\x24\x23\x22\x21\x20\x1f\x1e\x1d\x1c"
			"\x1b\x1a\x19\x18\x17\x16\x15\x14\x13\x12\x11\x10"
			"\x0f\x0e\x0d\x0c\x0b\x0a\x09\x08\x07\x06\x05\x04"
			"\x03\x02\x01\x00"
		),
		sized(
			"//79/Pv6+fj39vX08/Lx8O/u7ezr6uno5+bl5OPi4eDf3t3c29rZ2NfW1dTT0tHQz87NzMvKycjH"
			"xsXEw8LBwL++vby7urm4t7a1tLOysbCvrq2sq6qpqKempaSjoqGgn56dnJuamZiXlpWUk5KRkI+O"
			"jYyLiomIh4aFhIOCgYB/fn18e3p5eHd2dXRzcnFwb25tbGtqaWhnZmVkY2JhYF9eXVxbWllYV1ZV"
			"VFNSUVBPTk1MS0pJSEdGRURDQkFAPz49PDs6OTg3NjU0MzIxMC8uLSwrKikoJyYlJCMiISAfHh0c"
			"GxoZGBcWFRQTEhEQDw4NDAsKCQgHBgUEAwIBAA=="
		)
	}
};

Test(base64_encoded_size)
{
	test->equality(0, base64_encoded_size(0));
	test->equality(4, base64_encoded_size(1));
	test->equality(4, base64_encoded_size(2));
	test->equality(4, base64_encoded_size(3));
	test->equality(8, base64_encoded_size(4));
}

Test(base64_decoded_size)
{
	test->equality(0, base64_decoded_size(0));
	test->equality(3, base64_decoded_size(1));
	test->equality(3, base64_decoded_size(2));
	test->equality(3, base64_decoded_size(3));
	test->equality(3, base64_decoded_size(4));
	test->equality(6, base64_decoded_size(5));
}

Test(base64_indexes)
{
	// Clamps
	test->equality(128, sizeof(base64_value_index));
	test->equality(128, strlen(base64_digit_index));

	for (int i = 0; i < 64; ++i)
	{
		test->equality(i, base64_value(base64_digit(i)));
	}

	// Padding is decoded as zero.
	test->equality(0, base64_value('='));

	// >63 signals invalid digit.
	test->equality(64, base64_value('\0'));
	test->equality(64, base64_value('\x7f'));
}

Test(base64_encode_unit)
{
	uint8_t e[5];
	base64_encode_unit(e, "\0\0\0");
	test->memcmp("AAAA", e, 4);
}

Test(base64_encode)
{
	for (int i = 0; i < sizeof(samples) / sizeof(sstrpair_t); ++i)
	{
		char *buf;
		size_t digitcount;

		buf = base64_encode(&digitcount, samples[i].decoded, samples[i].dlength);
		test->memcmp(samples[i].encoded, buf, samples[i].elength);

		// Some samples intentionally discard padding; validate their insertion.
		if (samples[i].elength < digitcount)
		{
			int j = samples[i].elength;

			// Handle error case samples.
			if (j == 1 && buf[j] == 'A')
				++j;

			for (; j < digitcount; ++j)
				test->equality('=', buf[j]);
		}
		else
			test->equality(samples[i].elength, digitcount);

		BASE64_FREE(buf);
		buf = NULL;
	}
}

Test(base64_decode_unit)
{
	uint8_t e[4];
	base64_decode_unit(e, "AAAA");
	test->memcmp("\x00\x00\x00", e, 3);

	base64_decode_unit(e, "/w==");
	test->memcmp("\xFF", e, 1);
}

Test(base64_decode)
{
	for (int i = 0; i < sizeof(samples) / sizeof(sstrpair_t); ++i)
	{
		char *buf;
		size_t bytecount;
		buf = base64_decode(&bytecount, samples[i].encoded, samples[i].elength);
		test->memcmp(samples[i].decoded, buf, samples[i].dlength);
		test->equality(samples[i].dlength, bytecount);

		BASE64_FREE(buf);
		buf = NULL;
	}
}

Test(base64_recode_string)
{
	const char *string = "Testing the single argument form.";
	char *b64m = base64_encode_string(string);

	test->strcmp(string, base64_decode_string(b64m));
}

Test(base64_recode_constant)
{
	char *dm = base64_decode_constant("ZW5jb2RlZCBjb25zdGFudCBzdHJpbmc=");
	char *b64m = base64_encode_constant("encoded constant string");

	test->strcmp(dm, base64_decode_string(b64m));
	test->strcmp(b64m, base64_encode_string(dm));
}

Test(base64_data_uri)
{
	const char *const prefix = "data:text/plain;base64,";
	const char *const message = "base64 encoded message string.";
	char *uri;

	uri = base64_data_uri_string("text/plain", message);
	test->memcmp(prefix, uri, strlen(prefix));
	test->strcmp(uri + strlen(prefix), base64_encode_string(message));
	BASE64_FREE(uri);

	uri = base64_data_uri_string("text/plain", message);
	test->strcmp("data:type;base64,AA==", base64_data_uri_constant("type", "\0"));
}

static void
_extend_buf(void *context, uint8_t *data, size_t length)
{
	uint8_t **handle = context;
	memcpy(*handle, data, length);
	*handle += length;
}
#define bte(S, C, ...) base64_transfer_encoded(S, _extend_buf, C, __VA_ARGS__, NULL)

Test(base64_transmit_encoded)
{
	const uint8_t *expect =
		"a2FrZQp0ZXN0YmFzZTY0"
		"a2FrZQp0ZXN0YmFzZTY0"
		"a2FrZQp0ZXN0YmFzZTY0";
	uint8_t hold[512];
	uint8_t *handle = hold;
	uint8_t state[4] = {0,};
	uint32_t r = 0;

	#define S(X) (struct iovec[2]){(struct iovec){X, sizeof(X)-1}, (struct iovec){NULL, 0}}
	r += bte(state, &handle, S(""), S("kake\n"), S("test"), S("base64"));
	r += bte(state, &handle, S("kake\n"), S("test"), S("base64"));
	r += bte(state, &handle, S("k"), S("a"));
	r += bte(state, &handle, S("k"));
	r += bte(state, &handle, S("e"));
	r += bte(state, &handle, S("\n"));
	r += bte(state, &handle, S("t"));
	r += bte(state, &handle, S("e"));
	r += bte(state, &handle, S("st"));
	r += bte(state, &handle, S("base64"), S(""));
	r += bte(state, &handle, (struct iovec[2]){(struct iovec){(char *)state, 0}, (struct iovec){NULL, 0}});
	#undef sstr

	test->memcmp(expect, hold, sizeof(expect) - 1);
	test->equality(strlen(expect), r);
}
