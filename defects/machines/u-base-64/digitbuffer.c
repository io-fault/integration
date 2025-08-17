/**
	// Validate fault/base-64.h digit buffer.
*/
#include <fault/libc.h>

#define TEST_SUITE_EXTENSION
#include <fault/test.h>
#include <fault/base-64.h>

Test(base64_seek_digit)
{
	char *msg = base64_encode_string("A fragmented base-64 message.");
	char *split_message;
	size_t msglen = strlen(msg), offset = 0;

	asprintf(&split_message, ":\n\t%.8s \\\n\t%s\n", msg, msg+8);

	test->equality(msglen, base64_seek_exception(msg, msglen, msglen));

	offset = base64_seek_digit(split_message, offset, msglen);
	test->equality(3, offset);
	test->memcmp(msg, split_message + offset, 8);

	offset = base64_seek_digit(split_message, offset + 8, msglen);
	test->memcmp(msg + 8, split_message + offset, strlen(msg) - 8);

	BASE64_FREE(msg);
	free(split_message);
}

Test(base64_seek_exception)
{
	char *msg = "a!---a@aa#";
	size_t offset = 0, msglen = strlen(msg);

	test->equality(msglen, base64_seek_exception(msg, msglen, msglen));

	offset = base64_seek_exception(msg, offset, msglen);
	test->equality('!', msg[offset]);
	test->equality(offset, base64_seek_exception(msg, offset, msglen));

	offset = base64_seek_exception(msg, offset+1, msglen);
	test->equality('-', msg[offset]);
	test->equality(offset, base64_seek_exception(msg, offset, msglen));

	test->equality('-', msg[offset+0]);
	test->equality('-', msg[offset+1]);
	test->equality('-', msg[offset+2]);

	offset = base64_seek_exception(msg, offset+3, msglen);
	test->equality('@', msg[offset]);
	test->equality('a', msg[offset-1]);
	test->equality(offset, base64_seek_exception(msg, offset, msglen));

	offset = base64_seek_exception(msg, offset+1, msglen);
	test->equality('#', msg[offset]);
	test->equality(offset, base64_seek_exception(msg, offset, msglen));
}

Test(base64_buffer_digits)
{
	char *msg = base64_encode_string("A fragmented base-64 message.");
	char *split_message;
	size_t msglen, offset = 0;
	struct Base64_DigitBuffer dbuf;
	char *data;
	size_t readbytes;

	msglen = asprintf(&split_message, ":\n\t%.8s \\\n\t%s\n", msg, msg+8);
	base64_digitbuffer_initialize(&dbuf, 128);
	base64_digitbuffer_set_message(&dbuf, split_message, msglen);

	// Cycle on boundary.
	test->equality(true, base64_buffer_digits(&dbuf));
	test->memcmp(dbuf.d_buffer, msg, strlen(msg));
	base64_digitbuffer_cycle(&dbuf);

	// Next message.
	test->equality(false, base64_buffer_digits(&dbuf));
}

Test(base64_decode_fragments)
{
	char data[256];
	char *tmp, *p1, *p2, *p3, *p4;
	char *encoded = BASE64_MALLOC(base64_encoded_size(256));
	char *decoded = NULL;
	size_t el, dl;

	for (int i = 0; i < 256; ++i)
		data[i] = (char) i;

	el = base64_encode_memory(encoded, data, 256);
	dl = base64_decode_fragments(&decoded, 0, encoded, NULL);

	test->memcmp(decoded, data, 256);
	test->equality(256, dl);

	tmp = base64_encode(&el, data+0, 66);
	asprintf(&p1, "\t\t%s \\\n", tmp);
	BASE64_FREE(tmp);

	tmp = base64_encode(&el, data+66, 66);
	asprintf(&p2, "\t\t\t  %s   \\\n", tmp);
	BASE64_FREE(tmp);

	tmp = base64_encode(&el, data+66+66, 66);
	asprintf(&p3, "\t\t\t  %s   \\\n", tmp);
	BASE64_FREE(tmp);

	tmp = base64_encode(&el, data+66+66+66, 58);
	asprintf(&p4, "\t\t\t  %s   \\\n", tmp);
	BASE64_FREE(tmp);

	test->equality(256, base64_decode_fragments(&decoded, 0, p1, p2, p3, p4, NULL));
	test->memcmp(decoded, data, 256);

	BASE64_FREE(encoded);
	BASE64_FREE(decoded);
	free(p1);
	free(p2);
	free(p3);
	free(p4);
}

/**
	// Similar to the previous test, but consecutive terminated messages.
*/
Test(base64_decode_fragments_multiple_messages)
{
	char data[256];
	char *tmp, *p1, *p2, *p3, *p4;
	char *decoded = NULL;
	size_t el;

	for (int i = 0; i < 256; ++i)
		data[i] = (char) i;

	tmp = base64_encode(&el, data+0, 64);
	asprintf(&p1, "\t\t%s \\\n", tmp);
	BASE64_FREE(tmp);

	tmp = base64_encode(&el, data+64, 64);
	asprintf(&p2, "\t\t\t  %s   \\\n", tmp);
	BASE64_FREE(tmp);

	tmp = base64_encode(&el, data+64+64, 64);
	asprintf(&p3, "\t\t\t  %s   \\\n", tmp);
	BASE64_FREE(tmp);

	tmp = base64_encode(&el, data+64+64+64, 64);
	asprintf(&p4, "\t\t\t  %s   \\\n", tmp);
	BASE64_FREE(tmp);

	test->equality(256, base64_decode_fragments(&decoded, 0, p1, "", p2, "", p3, p4, NULL));
	test->memcmp(decoded, data, 256);

	BASE64_FREE(decoded);
	free(p1);
	free(p2);
	free(p3);
	free(p4);
}

/**
	// Validate empty message.
*/
Test(base64_decode_fragments_zero)
{
	char data[0] = "";
	char *decoded = NULL;
	size_t el;

	test->equality(0, base64_decode_fragments(&decoded, 0, "", "", NULL));
	test->memcmp(decoded, data, 0);

	BASE64_FREE(decoded);
}

/**
	// Validate one sequence message with some skipping.
*/
Test(base64_decode_fragments_one_sequence)
{
	char data[2] = "\0";
	char *decoded = NULL;
	size_t el;

	test->equality(1, base64_decode_fragments(&decoded, 0, "!@#$%", " AA== ", NULL));
	test->memcmp(decoded, data, 1);

	BASE64_FREE(decoded);
}

/**
	// Validate two sequence message with some skipping.
*/
Test(base64_decode_fragments_two_sequence)
{
	char data[2] = "\0\0";
	char *decoded = NULL;
	size_t el;

	test->equality(2, base64_decode_fragments(&decoded, 0, "!AA ==  !@#$%", " AA== ", NULL));
	test->memcmp(decoded, data, 2);

	BASE64_FREE(decoded);
}

/**
	// Validate handling of disparate padding.
*/
Test(base64_decode_fragments_isolated_padding)
{
	char data[2] = "\0\0";
	char *decoded = NULL;
	size_t el;

	test->equality(2, base64_decode_fragments(&decoded, 0, "!AA =  =!@#$%", " AA == ", NULL));
	test->memcmp(decoded, data, 2);

	BASE64_FREE(decoded);
}
