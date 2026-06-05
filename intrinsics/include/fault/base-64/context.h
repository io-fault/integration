const static uint8_t * const base64_digit_index = (const uint8_t *)
	"ABCDEFGHIJKLMNOPQRSTUVWXYZ"
	"abcdefghijklmnopqrstuvwxyz"
	"0123456789+/=============="
	"=========================="
	"========================";

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

struct Base64_DigitBuffer {
	size_t d_buffer_length;
	size_t d_buffer_offset;

	size_t d_message_length;
	size_t d_message_offset;

	uint8_t *d_buffer;
	const uint8_t *d_message;
};

typedef void (*base64_transfer_t)(void *context, uint8_t *digits, size_t count);
