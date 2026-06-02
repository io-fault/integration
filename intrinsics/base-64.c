/**
	// Base-64 encoder, decoder, and digit buffer for sparse decoding.

	// [ Integration Control Defines ]
	// /BASE64_MALLOC/
		// A malloc selection macro.
	// /BASE64_REALLOC/
		// A realloc selection macro. Only used by &base64_decode_fragments.
	// /BASE64_FREE/
		// A malloc selection macro.
*/
#ifndef _FAULT_BASE_64_H_
#define _FAULT_BASE_64_H_

// API (can be static inline or exported)
#ifndef BASE64_API
	#define BASE64_API(TYPE) static inline TYPE
#endif

// Internal Interfaces (should be static inline)
#ifndef BASE64_ISI
	#define BASE64_ISI(TYPE) static inline TYPE
#endif

#ifndef BASE64_MALLOC
	#define BASE64_MALLOC(S) malloc(S)
#endif

#ifndef BASE64_REALLOC
	#define BASE64_REALLOC(P, S) realloc(P, S)
#endif

#ifndef BASE64_FREE
	#define BASE64_FREE(P) free(P)
#endif

/**
	// Index to identify the base-64 digit that represents
	// a 6-bit value. The pad characters are considered
	// out of bounds, but are generally unused.
*/
const static uint8_t * const base64_digit_index = (const uint8_t *)
	"ABCDEFGHIJKLMNOPQRSTUVWXYZ"
	"abcdefghijklmnopqrstuvwxyz"
	"0123456789+/=============="
	"=========================="
	"========================";

/**
	// Index to identify the 6-bit value of a base-64 digit.

	// The pad character is considered zero under decoding and
	// is relied upon.
*/
const static uint8_t base64_value_index[128] = {
	// 0-39
	64, 64, 64, 64, 64, 64, 64, 64, 64, 64,
	64, 64, 64, 64, 64, 64, 64, 64, 64, 64,
	64, 64, 64, 64, 64, 64, 64, 64, 64, 64,
	64, 64, 64, 64, 64, 64, 64, 64, 64, 64,

	64, 64, 64, // 40-42
	// 43: "+"
	62,
	64, 64, 64, // 44-46
	// 47: "/"
	63,
	// 48-57, "0-9"
	52, 53, 54, 55, 56, 57, 58, 59, 60, 61,

	// 58-60
	64, 64, 64,
	// 61: "="
	0,
	// 62-64
	64, 64, 64,

	// 65-89: A-Z
	0, 1, 2, 3, 4, 5, 6, 7, 8, 9,
	10, 11, 12, 13, 14, 15, 16, 17, 18, 19,
	20, 21, 22, 23, 24, 25,

	// 90-96
	64, 64, 64, 64, 64, 64,

	// 97-122: a-z
	26, 27, 28, 29, 30, 31, 32, 33, 34, 35,
	36, 37, 38, 39, 40, 41, 42, 43, 44, 45,
	46, 47, 48, 49, 50, 51,

	// 123-127
	64, 64, 64, 64, 64
};

/**
	// Lookup a base-64 6-bit value using the &base64_value_index.
*/
BASE64_ISI(uint8_t)
base64_value(int8_t digit)
{
	uint8_t v = base64_value_index[digit];
	return(v);
}

/**
	// Lookup a base-64 digit using the &base64_digit_index.
*/
BASE64_ISI(uint8_t)
base64_digit(int8_t value)
{
	uint8_t d = (uint8_t) base64_digit_index[value];
	return(d);
}

/**
	// Identify the maximum number of digits, bytes, needed to
	// represent the base-64 form of a binary data allocation
	// consisting of &encoded_size number of bytes.

	// The encoding interfaces here will normally allocate
	// a NUL-terminated maximum and append pad characters
	// when not a fully aligned on a multiple of three.
*/
BASE64_ISI(size_t)
base64_encoded_size(size_t decoded_size)
{
	size_t w = (decoded_size + 2) / 3;
	return (4 * w);
}

/**
	// Identify the maximum number of bytes needed to
	// represent the binary form of a base-64 encoded message
	// consisting of &encoded_size number of digits.

	// In cases where padding is present, the actual *usage*
	// may be one or two bytes less than what is returned.
	// The decoding interfaces here will normally allocate
	// a NUL-terminated maximum and return the usage size.
*/
BASE64_ISI(size_t)
base64_decoded_size(size_t encoded_size)
{
	size_t w = (encoded_size + 3) / 4;
	return (3 * w);
}

/**
	// Translate three bytes into their four, base-64, digit form.

	// 11111122 22223333 33444444
	// 87654321 87654321 87654321
*/
BASE64_ISI(void)
base64_encode_unit(uint8_t encoded[4], const uint8_t decoded[3])
{
	register uint8_t iv;

	encoded[0] = base64_digit(decoded[0] >> 2);
	encoded[3] = base64_digit(decoded[2] & (0xFF >> 2));

	iv = (decoded[0] & 3) << 4;
	iv |= decoded[1] >> 4;
	encoded[1] = base64_digit(iv);

	iv = decoded[1] & 0xF;
	iv <<= 2;
	iv |= decoded[2] >> 6;
	encoded[2] = base64_digit(iv);
}

/**
	// Translate four base-64 digits into their three byte form.
*/
BASE64_ISI(void)
base64_decode_unit(uint8_t decoded[3], const uint8_t encoded[4])
{
	register uint8_t iv;

	decoded[0] = base64_value(encoded[0]) << 2;
	iv = base64_value(encoded[1]);
	decoded[0] |= iv >> 4;

	decoded[1] = (iv & 0xF) << 4;
	iv = base64_value(encoded[2]);
	decoded[1] |= (iv >> 2);

	decoded[2] = iv << 6;
	iv = base64_value(encoded[3]);
	decoded[2] |= iv;
}

#define base64_encode_constant(S) base64_encode(&((int[]){0})[0], S, sizeof(S)-1)
#define base64_decode_constant(S) base64_decode(&((int[]){0})[0], S, sizeof(S)-1)

/**
	// Encode &length bytes of &source into &encoded.

	// [ Parameters ]
	// /encoded/
		// Buffer consisting of enough space to write the
		// encoded form of &source to. (&base_decoded_size)
	// /source/
		// Data to be encoded.
	// /length/
		// Number of bytes in &source that should be encoded.

	// [ Returns ]
	// Number of padding characters inserted at the end of &encoded.
*/
BASE64_API(uint8_t)
base64_encode_memory(uint8_t *encoded, const uint8_t *source, size_t length)
{
	size_t i, limit = length > 3 ? length - 3 : 0;
	uint8_t r = 0, *c;
	uint8_t final[3] = {0,0,0};

	c = encoded;
	for (i = 0; i < limit; i += 3)
	{
		base64_encode_unit(c, source + i);
		c += 4;
	}

	switch(length - i)
	{
		case 3:
			final[0] = *(source + i + 0);
			final[1] = *(source + i + 1);
			final[2] = *(source + i + 2);
			base64_encode_unit(c, final);
			r = 0;
		break;

		case 2:
			final[0] = *(source + i + 0);
			final[1] = *(source + i + 1);
			base64_encode_unit(c, final);
			c[3] = '=';
			r = 1;
		break;

		case 1:
			final[0] = *(source + i + 0);
			base64_encode_unit(c, final);
			c[2] = '=';
			c[3] = '=';
			r = 2;
		break;
	}

	return(r);
}

/**
	// Decode the &length base-64 digits in &source into &decoded.

	// [ Parameters ]
	// /decoded/
		// Buffer consisting of enough space to write the
		// decoded form of &source to. (&base64_decoded_size)
	// /source/
		// Data to be decoded.
	// /length/
		// Number of bytes in &source that should be encoded.

	// [ Returns ]
	// Number of excess bytes at the end of decoded data.

	// Subtract this number from `base64_decoded_size(encoded_length)`
	// to get the exact byte count of data.
*/
BASE64_API(uint8_t)
base64_decode_memory(uint8_t *decoded, const uint8_t *source, size_t length)
{
	size_t i, limit = length >= 4 ? length - 4 : 0;
	uint8_t r = 0, *c = decoded;
	uint8_t final[4] = {'=', '=', '=', '='};

	for (i = 0; i < limit; i += 4)
	{
		base64_decode_unit(c, source + i);
		c += 3;
	}

	// Don't presume alignment and special case the final 1-4 bytes in
	// &source. Some extra effort is taken here to account for both
	// properly padded sequences, erroneous padding, and truncated
	// sequences.
	switch(length - i)
	{
		case 4:
			final[0] = *(source + i + 0);
			final[1] = *(source + i + 1);
			final[2] = *(source + i + 2);
			final[3] = *(source + i + 3);

			if (final[3] == '=')
				r += 1;
			if (final[2] == '=')
				r += 1;
		break;

		case 3:
			final[0] = *(source + i + 0);
			final[1] = *(source + i + 1);
			final[2] = *(source + i + 2);
			final[3] = '=';

			r = 1;
			if (final[2] == '=')
				r += 1;
		break;

		case 2:
			final[0] = *(source + i + 0);
			final[1] = *(source + i + 1);
			final[2] = '=';
			final[3] = '=';
			r = 2;
		break;

		case 1:
			// Not advisable.
			final[0] = *(source + i + 0);
			final[1] = '=';
			final[2] = '=';
			final[3] = '=';
			r = 2;
		break;

		case 0:
			// Zero length source.
		break;
	}

	base64_decode_unit(c, final);
	return(r);
}

/**
	// Encode &source of &length bytes into a new memory allocation
	// of base-64 digits.

	// [ Parameters ]
	// /digitcount/
		// The exact number of encoded digits written into the new allocation.
		// Includes any padding bytes.
	// /source/
		// The data that should be encoded.
	// /length/
		// Number of bytes in &source that should be encoded.

	// [ Returns ]
	// Pointer to the new allocation with &digitcount holding the number
	// of base-64 digits written into it.
*/
BASE64_API(uint8_t *)
base64_encode(size_t *digitcount, const uint8_t *source, size_t length)
{
	size_t el = base64_encoded_size(length);
	uint8_t *em;

	em = (uint8_t *) BASE64_MALLOC(el + 1);
	if (em == NULL)
		return(NULL);
	em[el] = '\0'; // Safety.

	*digitcount = el;
	base64_encode_memory(em, source, length);
	return(em);
}

/**
	// Decode &source of &length bytes (base-64 digits) into
	// a new memory allocation.

	// [ Parameters ]
	// /bytecount/
		// The exact number of decoded bytes written into the new allocation.
	// /source/
		// The base-64 encoded data.
	// /length/
		// Number of base-64 digits, bytes, in &source.

	// [ Returns ]
	// Pointer to the new allocation with &bytecount holding the number
	// of bytes written into it.
*/
BASE64_API(uint8_t *)
base64_decode(size_t *bytecount, const uint8_t *source, size_t length)
{
	size_t dl = base64_decoded_size(length);
	uint8_t *dm;

	dm = (uint8_t *) BASE64_MALLOC(dl + 1);
	if (dm == NULL)
		return(NULL);
	dm[dl] = '\0'; // Safety.

	*bytecount = dl - base64_decode_memory(dm, source, length);
	return(dm);
}

/**
	// Encode the NUL-terminated string as base-64.

	// [ Returns ]
	// NUL-terminated string allocated with &BASE64_MALLOC
*/
BASE64_API(char *)
base64_encode_string(const char *string)
{
	size_t i;
	return((char *) base64_encode(&i, (const uint8_t *) string, strlen(string)));
}

/**
	// Decode the NUL-terminated base-64 digits.

	// [ Returns ]
	// NUL-terminated string allocated with &BASE64_MALLOC
*/
BASE64_API(char *)
base64_decode_string(const char *string)
{
	size_t i;
	return((char *) base64_decode(&i, (const uint8_t *) string, strlen(string)));
}

/**
	// Seek the next base-64 digit from &offset in &message.

	// [ Parameters ]
	// /message/
		// Memory to search in.
	// /offset/
		// Offset from &message to start seeking.
	// /length/
		// Size of &message in bytes.

	// [ Returns ]
	// The offset of the next valid digit from &offset or &length if none were found.
*/
BASE64_ISI(size_t)
base64_seek_digit(const uint8_t *message, size_t offset, size_t length)
{
	for (size_t i = offset; i < length; ++i)
	{
		char c = message[i];

		if (c >= 128)
			continue;

		switch (base64_value(c))
		{
			case 64:
			break;

			default:
				return(i);
			break;
		}
	}

	return(length);
}

/**
	// Seek the next byte from &offset in &messsage that is not a base-64 digit.

	// [ Parameters ]
	// /message/
		// Memory to search in.
	// /offset/
		// Offset from &message to start seeking.
	// /length/
		// Size of &message in bytes.

	// [ Returns ]
	// The offset of the next invalid digit byte from &offset or &length if none were found.
*/
BASE64_ISI(size_t)
base64_seek_exception(const uint8_t *message, size_t offset, size_t length)
{
	for (size_t i = offset; i < length; ++i)
	{
		char c = message[i];

		if (c >= 128)
			return(i);

		switch (base64_value(c))
		{
			case 64:
				return(i);
			case 0:
				if (c == '=')
				{
					if (i + 1 < length)
					{
						// Check consecutive.
						if (message[i+1] == '=')
							return(i+2);
					}
					else
						return(i+1);
				}
			break;
		}
	}

	return(length);
}

/**
	// State used by &base64_buffer_digits. While a few abstractions
	// are provided to control this structure, it is not intended
	// to be opaque.

	// [ Elements ]
	// /d_buffer_length/
		// Allocation size of &d_buffer.
	// /d_buffer_offset/
		// The current write position of buffered digits in &d_buffer.
		// The difference between &d_buffer_length being the remaining space.
	// /d_message_length/
		// Maximum number of bytes to process in &d_message.
	// /d_message_offset/
		// Current read position in &d_message.
	// /d_buffer/
		// The buffer holding the digits identified in &d_message.
		// The allocation should be a multiple of four in order to
		// allow buffer cycle events
	
*/
struct Base64_DigitBuffer {
	size_t d_buffer_length;
	size_t d_buffer_offset;

	size_t d_message_length;
	size_t d_message_offset;

	uint8_t *d_buffer;
	const uint8_t *d_message;
};

/**
	// Initialize a &Base64_DigitBuffer structure allocating
	// &dbuf.d_buffer with four times the given &seqlimit.
*/
BASE64_ISI(void)
base64_digitbuffer_initialize(struct Base64_DigitBuffer *dbuf, size_t seqlimit)
{
	dbuf->d_buffer_length = 4 * seqlimit;
	dbuf->d_buffer_offset = 0;
	dbuf->d_buffer = (uint8_t *) BASE64_MALLOC(dbuf->d_buffer_length);

	dbuf->d_message = NULL;
	dbuf->d_message_length = 0;
	dbuf->d_message_offset = 0;
}

/**
	// Reset the buffer offset to zero.
	// Used after the buffer's digits have been processed, decoded, and
	// is ready for re-use with &base64_buffer_digits.
*/
BASE64_ISI(void)
base64_digitbuffer_cycle(struct Base64_DigitBuffer *dbuf)
{
	dbuf->d_buffer_offset = 0;
}

/**
	// Update the &dbuf.d_message and &dbuf.d_message_length fields with a new
	// &message and &length after initialization or in response to
	// &base64_buffer_digits returns &false.
*/
BASE64_ISI(void)
base64_digitbuffer_set_message(struct Base64_DigitBuffer *dbuf, const uint8_t *message, size_t length)
{
	dbuf->d_message = message;
	dbuf->d_message_offset = 0;
	dbuf->d_message_length = length;
}

/**
	// Release the &dbuf.d_buffer memory allocation and zero its related
	// offset and length fields.
*/
BASE64_ISI(void)
base64_digitbuffer_release(struct Base64_DigitBuffer *dbuf)
{
	dbuf->d_buffer_length = 0;
	dbuf->d_buffer_offset = 0;
	BASE64_FREE(dbuf->d_buffer);
	dbuf->d_buffer = NULL;
}

/**
	// Buffer valid digits into &dbuf.d_buffer from &dbuf.d_message while skipping invalids.
	// Alignment, of full buffers, is guaranteed by the buffer size being a multiple of four.
	// Early cycling is performed when pad, `=`, characters are encountered.

	// Buffers with digit sequences starting with pad characters are discarded.

	// [ Parameters ]
	// /dbuf/
		// Digit buffer state to advance.

	// [ Returns ]
	// &true when the &Base64_DigitBuffer.d_buffer is full and should be cycled.
	// &false when the &Base64_DigitBuffer.d_message has been fully processed and
	// either buffering is complete or &base64_digitbuffer_set_message should
	// be used to continue buffering digits.
*/
BASE64_API(bool)
base64_buffer_digits(struct Base64_DigitBuffer *dbuf)
{
	uint8_t *rbuf;
	size_t start, stop, q, max;

	max = dbuf->d_buffer_length - dbuf->d_buffer_offset;
	while (dbuf->d_buffer_offset < dbuf->d_buffer_length)
	{
		start = base64_seek_digit(dbuf->d_message, dbuf->d_message_offset, dbuf->d_message_length);
		stop = base64_seek_exception(dbuf->d_message, start, dbuf->d_message_length);

		q = stop - start;
		if (q > max)
		{
			dbuf->d_message_offset = start + max;
			memcpy(dbuf->d_buffer + dbuf->d_buffer_offset, dbuf->d_message + start, max);
			return(true);
		}
		else
		{
			dbuf->d_message_offset = stop;
			memcpy(dbuf->d_buffer + dbuf->d_buffer_offset, dbuf->d_message + start, q);
			dbuf->d_buffer_offset += q;
			max -= q;

			// Terminate if base64_seek_exception detected a boundary.
			if (dbuf->d_buffer[dbuf->d_buffer_offset-(dbuf->d_buffer_offset > 0 ? 1 : 0)] == '=')
			{
				if (dbuf->d_buffer[0] != '=')
					return(true);

				// Ignore errant padding characters.
				// An odd case, but a preferrable choice to inserting NULLs.
				// This case is created by pad termination in &base64_buffer_digits.
				// assert(dbuf->d_buffer_offset < 3);
				base64_digitbuffer_cycle(dbuf);
				max = dbuf->d_buffer_length - dbuf->d_buffer_offset;
			}
		}

		// End of message.
		if (stop >= dbuf->d_message_length)
			break;
	}

	return(false);
}

/**
	// Buffer and decode the base-64 digits *found* in the strings given
	// as variable arguments. A slightly high-level interface to the
	// digit buffer and decoding.

	// Continuations are not supported by this interface and
	// decoding will force pad the digits after processing
	// the last source.

	// [ Parameters ]
	// /decoded/
		// The &BASE64_MALLOC allocated memory to write the decoded
		// base-64 into. &BASE64_REALLOC calls may update this pointer
		// to fit new data.
	// /length/
		// The number of already processed bytes in &decoded and,
		// likely, allocation size.
	// /.../
		// NULL argument terminated list of NUL-terminated strings
		// to collect base-64 digits from.

	// [ Returns ]
	// The new usage length of the &decoded data.
*/
BASE64_API(size_t)
base64_decode_fragments(uint8_t **decoded, size_t length, ...)
{
	const uint8_t *msg;
	size_t decoded_size = length;
	struct Base64_DigitBuffer dbuf;
	va_list args;

	base64_digitbuffer_initialize(&dbuf, 512);

	if (length == 0 && *decoded == NULL)
	{
		*decoded = (uint8_t *) BASE64_MALLOC(4);
		(*decoded)[0] = 0;
		(*decoded)[1] = 0;
		(*decoded)[2] = 0;
		(*decoded)[3] = 0;
	}

	va_start(args, length);
	msg = va_arg(args, const uint8_t *);

	while (msg != NULL)
	{
		base64_digitbuffer_set_message(&dbuf, msg, strlen((const char *) msg));

		while (base64_buffer_digits(&dbuf))
		{
			size_t dsize = base64_decoded_size(dbuf.d_buffer_offset);

			decoded_size += dsize;
			*decoded = (uint8_t *) BASE64_REALLOC(*decoded, decoded_size);

			decoded_size -= base64_decode_memory((*decoded) + length, dbuf.d_buffer, dbuf.d_buffer_offset);
			length = decoded_size;
			base64_digitbuffer_cycle(&dbuf);
		}

		msg = va_arg(args, const uint8_t *);
	}

	va_end(args);

	if (dbuf.d_buffer_offset > 0)
	{
		size_t dsize = base64_decoded_size(dbuf.d_buffer_offset);
		decoded_size += dsize;
		*decoded = (uint8_t *) BASE64_REALLOC(*decoded, decoded_size);

		decoded_size -= base64_decode_memory((*decoded) + length, dbuf.d_buffer, dbuf.d_buffer_offset);
	}

	base64_digitbuffer_release(&dbuf);
	return(decoded_size);
}

/**
	// Construct a base-64 encoded data URI.

	// [ Parameters ]
	// /media_type/
		// The media type to insert before the data.
	// /data/
		// The data to encode as base-64.
	// /length/
		// Number of bytes in &data that should be encoded.

	// [ Returns ]
	// New allocation (&BASE64_MALLOC) containing the constructed URI.
*/
BASE64_API(uint8_t *)
base64_data_uri(const uint8_t *media_type, const uint8_t *data, size_t length)
{
	uint8_t *uri;
	size_t ul = sizeof("data:;base64,") + strlen((const char *) media_type);
	size_t el = base64_encoded_size(length);

	uri = (uint8_t *) BASE64_MALLOC(ul + el);
	ul = snprintf((char *) uri, ul, "data:%s;base64,", media_type);
	base64_encode_memory(uri + ul, data, length);

	return(uri);
}

#define base64_data_uri_string(MT, D) base64_data_uri(MT, D, strlen(D))
#define base64_data_uri_constant(MT, D) base64_data_uri(MT, D, sizeof(D)-1)

typedef void (*base64_transfer_t)(void *context, uint8_t *digits, size_t count);

/**
	// Continuously transfer encoded source data to a target function and context.

	// [ Parameters ]
	// /state/
		// Four byte memory allocation holding the partial writes to be
		// completed by the next call.
	// /tf/
		// Tranfer function taking &context, the (base64) digit count, byte length,
		// and the digits buffer containing the last set of encoded digits.

		// Called whenever there is one or more encoded units to be transferred
		// or when the flush signal is received with non-zero &state.
	// /context/
		// The context pointer given as &tf' first argument.
	// /vl/
		// Terminated by a `NULL, 0` pair or the &state pointer and zero size.
		// When terminated by the latter, &state will be flushed and padding bytes
		// will be added to the transfer.

	// [ Returns ]
	// The total number of *encoded* bytes transferred to &tf.
*/
BASE64_API(size_t)
base64_transfer_encoded_v(uint8_t state[4], base64_transfer_t tf, void *context, struct iovec *vl)
{
	const uint8_t eunit = 4;
	const uint8_t dunit = 3;

	uint8_t write_buffer[eunit * 40]; // Alignment required.
	uint8_t *rbp, *wbp = write_buffer;
	size_t total = 0, available = 0, capacity = sizeof(write_buffer);

	// Buffer needs non-zero capacity and be base-64 digit unit aligned.
	assert(sizeof(write_buffer) > 0);
	assert(sizeof(write_buffer) % eunit == 0);

	not_terminated:
	while (available = vl->iov_len)
	{
		rbp = (uint8_t *) vl->iov_base;
		++vl;

		if (state[0] > 0)
		{
			// Finish partial.
			size_t cp, rb = dunit;

			// Partial.
			assert(state[0] < dunit);

			// Identify the amount to copy. (Available may be smaller than remaining)
			rb -= state[0];
			cp = available > rb ? rb : available;

			// Integrate into state.
			memcpy(state + 1 + state[0], rbp, cp);
			state[0] += cp;
			rbp += cp;
			available -= cp;

			// Not enough data for a unit? Continue or exit for more.
			if (state[0] < dunit)
				continue;

			// Transfer unit and update write position.
			base64_encode_unit(wbp, state+1);
			wbp += eunit;
			capacity -= eunit;

			// Reset state.
			state[0] = 0; // Partial count.
			state[1] = 0;
			state[2] = 0;
			state[3] = 0;
		}
		else
		{
			// Partial or aligned.
			assert(state[0] == 0);
		}

		// Prepare remainder of data.
		state[0] = available % dunit;
		if (state[0] > 0)
		{
			// Carry last partial sequence in state for next iteration.
			memcpy(state+1, rbp + available - state[0], state[0]);
			available -= state[0]; // Aligned length.
		}

		// available is aligned(*dunit); transfer until done.
		while (available > 0)
		{
			size_t xfer;

			if (base64_encoded_size(available) > capacity)
				xfer = (capacity / eunit) * dunit; // Remaining space.
			else
				xfer = available; // Enough room for the encoded data.

			// Encode at write position and advance state.
			base64_encode_memory(wbp, rbp, xfer);
			available -= xfer;
			rbp += xfer;

			// Encoded size in the write buffer.
			xfer = base64_encoded_size(xfer);
			capacity -= xfer;
			wbp += xfer;

			// Flush write buffer if full.
			if (capacity == 0)
			{
				tf(context, write_buffer, sizeof(write_buffer));
				total += sizeof(write_buffer);

				// Reset write buffer.
				wbp = write_buffer;
				capacity = sizeof(write_buffer);
			}
			else
			{
				assert(capacity > 0);
				assert(capacity <= sizeof(write_buffer));
			}
		}
	}

	rbp = (uint8_t *) vl->iov_base;

	// Flush signal.
	if (state == rbp && state[0] > 0)
	{
		// Room for this should always be available given
		// an aligned write buffer as it's flushed when
		// the capacity is zero and the capacity is only
		// decremented by multiples of &eunit.
		assert(capacity >= eunit);

		base64_encode_memory(wbp, state+1, state[0]);
		state[0] = 0;
		wbp += eunit;
		capacity -= eunit;
	}
	else if (rbp != NULL)
	{
		// Zero length string. Continue processing at the next record.
		++vl;
		goto not_terminated;
	}

	// Flush any buffered writes and leave state to carry partials to the next call.
	if (capacity < sizeof(write_buffer))
	{
		size_t xfer = sizeof(write_buffer) - capacity;

		tf(context, write_buffer, xfer);
		total += xfer;
	}
	else
	{
		assert(capacity == sizeof(write_buffer));
	}

	return(total);
}

BASE64_API(size_t)
base64_transfer_encoded(uint8_t state[4], base64_transfer_t tf, void *context, ...)
{
	size_t r = 0;
	va_list vl;

	va_start(vl, context);
	do
	{
		struct iovec *iov = va_arg(vl, struct iovec *);
		if (iov == NULL)
			break;
		r += base64_transfer_encoded_v(state, tf, context, iov);
	} while(1);
	va_end(vl);

	return(r);
}
#endif
