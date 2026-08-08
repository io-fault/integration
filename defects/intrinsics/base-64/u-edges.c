/**
	// Tests analyzing base-64 edge cases.
*/
#include <fault/libc.h>
#include <fault/metrics.h>
#include <fault/test.h>
#include <fault/base-64.h>

#define bte(S, ...) base64_transfer_encoded(S, _ignore, NULL, __VA_ARGS__, NULL)
#define IOV(X) ((struct iovec){X, sizeof(X)-1})
#define ION ((struct iovec){NULL, 0})

static void
_ignore(void *context, uint8_t *data, size_t length)
{
	;
}

/**
	// Validate a flush of the write buffer when both
	// buffers have no space for more transfers.

	// (Check that the loop is unconditionally entered)
*/
Test(base64_transfer_encoded_zeros)
{
	uint8_t state[4] = {0,};
	uint32_t r = 0;

	#define bytes10 "1234567890"
	#define bytes40 bytes10 bytes10 bytes10 bytes10
	#define bytes117 bytes40 bytes40 bytes10 bytes10 bytes10 "1234567"

	// Must align with the internal write_buffer size in
	// &base64_transfer_encoded_v.
	r += bte(state, (struct iovec[3]){IOV(bytes117), IOV("890"), ION});
	test->equality(4 * 40, r);
	test->equality(0, state[0]);
}
