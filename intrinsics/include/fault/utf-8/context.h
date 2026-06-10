/**
	// UTF-8 decoding and encoding data structures and definitions.
*/

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
