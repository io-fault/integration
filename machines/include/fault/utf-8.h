/**
	// UTF-8 decoding and encoding tools.
*/
#ifndef _FAULT_UTF_8_H_
#define _FAULT_UTF_8_H_

/**
	// Visibility and linkage control define for the primary interfaces.
*/
#ifndef UTF8_API
	#define UTF8_API(TYPE) static inline TYPE
#endif

/**
	// Visibility and linkage control define for a few internal functions.
*/
#ifndef UTF8_ISI
	#define UTF8_ISI(TYPE) static inline TYPE
#endif

/**
	// Unused limit definition that may allow for larger, illegal, values to be converted.
*/
#ifndef UTF8_SEQUENCE_LIMIT
	#define UTF8_SEQUENCE_LIMIT 4
#endif

#define UTF8_CONTINUATION (2 << 6)
#define UTF8_SEQUENCE_1 (0)
// 0b110 << 5 | 5bits
#define UTF8_SEQUENCE_2 (3 << 1)
// 0b1110 << 4 | 4bits
#define UTF8_SEQUENCE_3 (0xF - 1)
// 0b11110 << 3 | 3bits
#define UTF8_SEQUENCE_4 (0xF << 1)

/**
	// Illegal (out of range) sequences.
*/
// 0b111110 << 2 | 2bits
#define UTF8_SEQUENCE_5 (0xF0 | (1 << 3))
// 0b1111110 << 1 | 1bit
#define UTF8_SEQUENCE_6 (0xF0 | (3 << 2))
// 0b11111110 << 0 | 0bit
#define UTF8_SEQUENCE_7 (0xFF - 1)
// 0b11111111 << i0 | 0bit
#define UTF8_SEQUENCE_8 (0xFF)

/**
	// Error list X-macro that sources UTF8Error enumeration and provides
	// error messages and formatting for detailed error reports.
*/
#define UTF8_ERRORS(U8_ERROR) \
	U8_ERROR(insufficient_data, "The sequence needs more data to identify the codepoint.") \
	U8_ERROR(unexpected_continuation, "A continuation byte was found outside of a sequence.") \
	U8_ERROR(missing_continuation, "The sequence is not composed of continuation bytes.") \
	U8_ERROR(invalid_sequence_length, "The sequence indicates a length beyond the 4-byte limit.") \
	U8_ERROR(value_out_of_range, "The codepoint value is outside of the expected range for the sequence.") \
	U8_ERROR(surrogate_character, "A codepoint in the surrogate range was identified.")

/**
	// Range macros identifying the valid range of a UTF-8 byte sequence;
	// inclusive on the start and exclusive on the stop.
*/
#define UTF8_VALID_RANGES(U8_VALID_RANGE) \
	U8_VALID_RANGE(1, 0x0, 0x80) \
	U8_VALID_RANGE(2, 0x80, 0x800) \
	U8_VALID_RANGE(3, 0x800, 0x10000) \
	U8_VALID_RANGE(4, 0x10000, 0x110000)

/**
	// Set of recognized UTF-8 errors.
*/
enum UTF8Error {
	utf8_error_none = 0,

	#define X(N, D) utf8_error_##N ,
		UTF8_ERRORS(X)
	#undef X

	utf8_error_sentinal
};

/**
	// Error structure noting the error type, the position within the sequence that
	// is the source of the error, and the offending sequence's bytes.
*/
typedef struct {
	enum UTF8Error errcode : 4;
	uint8_t errindex : 4;
	uint8_t errsequence[4];
} utf8_error_t;

/**
	// Look up the name of an error type.
*/
UTF8_API(const char *)
utf8_error_identifier(enum UTF8Error errid)
{
	switch (errid)
	{
		#define X(NAME, D) case utf8_error_##NAME : return(#NAME);
			UTF8_ERRORS(X)
		#undef X

		default:
			;
		break;
	}

	return(NULL);
}

/**
	// Look up the error message describing the type.
*/
UTF8_API(const char *)
utf8_error_message(enum UTF8Error errid)
{
	switch (errid)
	{
		#define X(NAME, D) case utf8_error_##NAME : return(D);
			UTF8_ERRORS(X)
		#undef X

		default:
			;
		break;
	}

	return(NULL);
}

/**
	// Whether the UTF-8 sequence fragment integer is a continuation byte.
*/
UTF8_API(bool)
utf8_continuation(uint8_t c)
{
	// Validate leading 0b10.
	return(c >> 6 == (1 << 1));
}

/**
	// The value of a UTF-8 sequence continuation.
*/
UTF8_API(uint8_t)
utf8_continuation_value(uint8_t c)
{
	// Zero leading 0b10; no validation.
	return(c & (0xFF >> 2));
}

/**
	// The value of the UTF-8 sequence initializor.
*/
UTF8_API(uint8_t)
utf8_sequence_value(uint8_t c, size_t seq_length)
{
	// Zero leading 0b110, 0b1110, or 0b11110. No validation.
	return(c & (0xFF >> (seq_length + 1)));
}

/**
	// Identify the length of the UTF-8 sequence using its initializor.
*/
UTF8_API(size_t)
utf8_identify_sequence_length(uint8_t c)
{
	// 0b110
	if (c >> 5 == UTF8_SEQUENCE_2)
		return(2);

	// 0b1110
	if (c >> 4 == UTF8_SEQUENCE_3)
		return(3);

	// 0b11110
	if (c >> 3 == UTF8_SEQUENCE_4)
		return(4);

	// Potentially invalid size.
	return(1);
}

/**
	// Check that &value is within the specified legal range for a UTF-8 sequence
	// of &length bytes.

	// [ Returns ]
	// /&false/
		// The &value is outside of the UTF-8 range identified by &length
		// or &length is not a legal size. (1-4).
	// /&true/
		// THe &value is within the UTF-8 range identified by &length.
*/
UTF8_API(bool)
utf8_range_valid(size_t length, uint32_t value)
{
	switch (length)
	{
		#define X(L, START, STOP) \
			case L: \
				if (value < START || value > STOP) \
					return(false); \
			break;

			UTF8_VALID_RANGES(X)
		#undef X

		default:
			// Invalid size.
			return(false);
		break;
	}

	return(true);
}

/**
	// Primary decoding function filling &cp with the codepoint identified at the beginning
	// of the &cv buffer that has at least &limit bytes that may be addressed by the function.

	// Codepoint identification never fails as invalid sequences are surrogate escaped.
	// The error conditions causing these escapes may be identified by checking if the
	// codepoint is within the escape range, `0xDC00` through `0xDCFF` inclusive, *and* that
	// the returned size is `1`. However, the &utf_error function can be used to automate this
	// and provide a &utf_error_t instance identifying the exact cause of the condition.

	// [ Parameters ]
	// /cv/
		// The buffer to read UTF-8 bytes from.
	// /limit/
		// The number of bytes available for interpreting in &cv.
		// The remaining number of bytes of data relative to &cv's position.

		// *Must* be `1` or more.

	// [ Returns ]
	// The number of bytes used to form the codepoint placed in &cp.

	// /cp/
		// The storage location to place the identified codepoint.
*/
UTF8_API(size_t)
utf8_identify_codepoint(uint32_t *cp, uint8_t *cv, size_t limit)
{
	size_t length = 1;
	uint32_t w = 0;

	assert(limit >= 1);

	// Switch on the leading two bits.
	// Single byte character, error, or start of sequence.
	switch (cv[0] >> 6)
	{
		// 0b00 or 0b01.
		case 0:
		case 1:
		{
			// 0b00 and 0b01.
			*cp = cv[0];
			return(1);
		}
		break;

		// 0b10.
		case (1 << 1) | 0:
		{
			// 0b10 continuation outside of sequence.
			goto error;
		}
		break;

		// 0b11.
		case (1 << 1) | 1:
		{
			length = utf8_identify_sequence_length(cv[0]);

			// 0b11, read size and subsequent bytes.
			if (limit < length)
			{
				// utf8_insufficient_data_error
				goto error;
			}
			else
			{
				// Continuation bytes must be checked here.

				switch (length)
				{
					case 2:
					{
						if (!utf8_continuation(cv[1]))
							goto error;

						// 11-bits
						w = utf8_sequence_value(cv[0], 2);
						w <<= 6;
						w |= utf8_continuation_value(cv[1]);
					}
					break;

					case 3:
					{
						if (!utf8_continuation(cv[1]))
							goto error;
						if (!utf8_continuation(cv[2]))
							goto error;

						// 16-bits
						w = utf8_sequence_value(cv[0], 3);
						w <<= 6;
						w |= utf8_continuation_value(cv[1]);
						w <<= 6;
						w |= utf8_continuation_value(cv[2]);
					}
					break;

					case 4:
					{
						if (!utf8_continuation(cv[1]))
							goto error;
						if (!utf8_continuation(cv[2]))
							goto error;
						if (!utf8_continuation(cv[3]))
							goto error;

						// 21-bits
						w = utf8_sequence_value(cv[0], 4);
						w <<= 6;
						w |= utf8_continuation_value(cv[1]);
						w <<= 6;
						w |= utf8_continuation_value(cv[2]);
						w <<= 6;
						w |= utf8_continuation_value(cv[3]);
					}
					break;

					default:
					{
						// Invalid length.
						goto error;
					}
				}
			}
		}
		break;
	}

	*cp = w;
	return(length);

	// Surrogates are expressed with 3-byte sequences, so callers
	// can identify (escaped) error cases by recognizing that a surrogate
	// was produced with a single byte.
	error:
	{
		*cp = 0xDC00 + cv[0];
		return(1);
	}
}

/**
	// Construct a &utf8_error_t using the given parameters and copying the sequence
	// codepoints from &cv into the &errsequence field.
*/
UTF8_API(utf8_error_t)
utf8_error_construct(enum UTF8Error code, uint8_t index, uint8_t *cv, size_t length, size_t limit)
{
	utf8_error_t err = {code, index};
	size_t j = limit < length ? limit : length;

	for (size_t i = 0; i < j; ++i)
		err.errsequence[i] = cv[i];

	return(err);
}

/**
	// Isolate the exact error that was compensated for by a &utf8_identify_codepoint call.

	// This function only reports errors regarding the interpreted data and leaves
	// all range checking to &utf8_error.
*/
UTF8_API(utf8_error_t)
utf8_identify_error(uint8_t *cv, size_t limit)
{
	assert(limit >= 1);

	// Switch on the leading two bits.
	// Single byte character, error, or start of sequence.
	switch (cv[0] >> 6)
	{
		// 0b00 or 0b01.
		case 0:
		case 1:
			// No error.
		break;

		// 0b10.
		case (1 << 1) | 0:
		{
			return((utf8_error_t) {utf8_error_unexpected_continuation, 0, cv[0]});
		}
		break;

		// 0b11.
		case (1 << 1) | 1:
		{
			size_t length = utf8_identify_sequence_length(cv[0]);

			if (limit < length)
			{
				return(utf8_error_construct(
					utf8_error_insufficient_data, length - limit,
					cv, length, limit
				));
			}
			else if (length < 2)
			{
				return(utf8_error_construct(
					utf8_error_invalid_sequence_length, 0,
					cv, length, limit
				));
			}
			else
			{
				for (size_t i = 1; i < length; ++i)
				{
					if (!utf8_continuation(cv[i]))
					{
						return(
							utf8_error_construct(
								utf8_error_missing_continuation, i,
								cv, length, limit
							)
						);
					}
				}
			}
		}
		break;
	}

	return((utf8_error_t) {utf8_error_none, 0, ""});
}

/**
	// Complete error check of &utf8_identify_codepoint results reporting invalid sequence
	// errors and range errors.

	// [ Usage ]
	#!syntax/c
		uint8_t cv[];
		size_t cd, limit = sizeof(cv);
		uint32_t cp = 0;
		utf8_error_t error;

		cd = utf8_identify_codepoint(&cp, cv, limit);
		error = utf8_error(cv, limit, cd, cp);
		switch (error.errcode)
		{
			case utf8_error_insufficient_data:
				//// More data needed for sequence.
			break;

			case utf8_error_none:
				//// Success.
			break;
		}

	// [ Returns ]
	// Error structure defining the error type and qualifying index or quantity.

	// /utf8_error_insufficient_data/
		// The &errindex identifies the number of missing bytes expected by the sequence.
	// /utf8_error_missing_continuation/
		// The &errindex identifies the sequence relative byte that was not a continuation.
*/
UTF8_API(utf8_error_t)
utf8_error(uint8_t *cv, size_t limit, size_t length, uint32_t cp)
{
	switch (length)
	{
		case 1:
		{
			// 0xDCxx >> 8
			if (cp >> 8 == 0xDC)
			{
				// Surrogate escape with length of one identifies error condition.
				return(utf8_identify_error(cv, limit));
			}
		}
		break;

		case 3:
		{
			// Check for surrogate.
			if (cp >= 0xD800 && cp <= 0xDFFF)
			{
				return(utf8_error_construct(
					utf8_error_surrogate_character, 0,
					cv, 3, limit
				));
			}
		}
	}

	// Restrict ranges.
	switch (length)
	{
		#define X(L, START, STOP) \
			case L: \
				if (cp < START || cp >= STOP) \
					return(utf8_error_construct(utf8_error_value_out_of_range, 0, cv, length, limit)); \
			break;

		UTF8_VALID_RANGES(X)
		#undef X
	}

	return((utf8_error_t) {utf8_error_none, 0});
}

/**
	// Identify the sequence length required to represent the given codepoint.

	// [ Parameters ]
	// /cp/
		// The codepoint whose sequence length is being sought.

	// [ Returns ]
	// `0` when &cp is greater than or equal to `0x110000`, otherwise
	// the number of bytes needed to represent the UTF-8 sequence.
*/
UTF8_API(size_t)
utf8_sequence_length(uint32_t cp)
{
	if (cp < 0x80)
		return(1);

	if (cp < 0x800)
		return(2);

	if (cp < 0x10000)
		return(3);

	if (cp < 0x110000)
		return(4);

	return(0);
}

UTF8_ISI(size_t)
utf8_sequence_codepoint_1(uint8_t *cv, uint32_t cp)
{
	// 0b0
	cv[0] = (uint8_t) cp;
	return(1);
}

UTF8_ISI(size_t)
utf8_sequence_codepoint_2(uint8_t *cv, uint32_t cp)
{
	cv[1] = UTF8_CONTINUATION | (cp & (0xFF >> 2));
	cp >>= 6;

	// 0b110 << 5
	cv[0] = (UTF8_SEQUENCE_2 << 5) | (uint8_t) cp;
	return(2);
}

UTF8_ISI(size_t)
utf8_sequence_codepoint_3(uint8_t *cv, uint32_t cp)
{
	cv[2] = UTF8_CONTINUATION | (cp & (0xFF >> 2));
	cp >>= 6;
	cv[1] = UTF8_CONTINUATION | (cp & (0xFF >> 2));
	cp >>= 6;

	// 0b1110 << 4
	cv[0] = (UTF8_SEQUENCE_3 << 4) | (uint8_t) cp;
	return(3);
}

UTF8_ISI(size_t)
utf8_sequence_codepoint_4(uint8_t *cv, uint32_t cp)
{
	cv[3] = UTF8_CONTINUATION | (cp & (0xFF >> 2));
	cp >>= 6;
	cv[2] = UTF8_CONTINUATION | (cp & (0xFF >> 2));
	cp >>= 6;
	cv[1] = UTF8_CONTINUATION | (cp & (0xFF >> 2));
	cp >>= 6;

	// 0b11110 << 4
	cv[0] = (UTF8_SEQUENCE_4 << 3) | (uint8_t) cp;
	return(4);
}

/**
	// Convert a codepoint into a UTF-8 sequence.

	// [ Parameters ]
	// /cp/
		// The codepoint to encode.

	// [ Returns ]
	// Number of bytes written into &cv.

	// /cv/
		// The buffer to write the sequence into.
		// It is presumed that 4-bytes are available for writing.
*/
UTF8_API(size_t)
utf8_sequence_codepoint(uint8_t *cv, uint32_t cp)
{
	switch (utf8_sequence_length(cp))
	{
		case 1:
			return(utf8_sequence_codepoint_1(cv, cp));
		case 2:
			return(utf8_sequence_codepoint_2(cv, cp));
		case 3:
		{
			// Restore error byte.
			if (cp >> 8 == 0xDC)
			{
				cv[0] = cp & 0xFF;
				return(1);
			}

			return(utf8_sequence_codepoint_3(cv, cp));
		}
		case 4:
			return(utf8_sequence_codepoint_4(cv, cp));
	}

	return(0);
}
#endif
