BASE64_API(uint8_t)
base64_encode_memory(uint8_t *encoded, const uint8_t *source, size_t length);

BASE64_API(uint8_t)
base64_decode_memory(uint8_t *decoded, const uint8_t *source, size_t length);

BASE64_API(uint8_t *)
base64_encode(size_t *digitcount, const uint8_t *source, size_t length);

BASE64_API(uint8_t *)
base64_decode(size_t *bytecount, const uint8_t *source, size_t length);

BASE64_API(char *)
base64_encode_string(const char *string);

BASE64_API(char *)
base64_decode_string(const char *string);

BASE64_API(bool)
base64_buffer_digits(struct Base64_DigitBuffer *dbuf);

BASE64_API(size_t)
base64_decode_fragments(uint8_t **decoded, size_t length, ...);

BASE64_API(uint8_t *)
base64_data_uri(const uint8_t *media_type, const uint8_t *data, size_t length);

BASE64_API(size_t)
base64_transfer_encoded_v(uint8_t state[4], base64_transfer_t tf, void *context, struct iovec *vl);

BASE64_API(size_t)
base64_transfer_encoded(uint8_t state[4], base64_transfer_t tf, void *context, ...);

BASE64_API(size_t)
base64_encoded_size(size_t decoded_size);

BASE64_API(size_t)
base64_decoded_size(size_t encoded_size);

#ifdef _FAULT_BASE64_INTERNAL_
BASE64_ISI(uint8_t)
base64_value(int8_t digit);

BASE64_ISI(uint8_t)
base64_digit(int8_t value);

BASE64_ISI(void)
base64_encode_unit(uint8_t encoded[4], const uint8_t decoded[3]);

BASE64_ISI(void)
base64_decode_unit(uint8_t decoded[3], const uint8_t encoded[4]);

BASE64_ISI(size_t)
base64_seek_digit(const uint8_t *message, size_t offset, size_t length);

BASE64_ISI(size_t)
base64_seek_exception(const uint8_t *message, size_t offset, size_t length);

BASE64_ISI(void)
base64_digitbuffer_initialize(struct Base64_DigitBuffer *dbuf, size_t seqlimit);

BASE64_ISI(void)
base64_digitbuffer_cycle(struct Base64_DigitBuffer *dbuf);

BASE64_ISI(void)
base64_digitbuffer_set_message(struct Base64_DigitBuffer *dbuf, const uint8_t *message, size_t length);

BASE64_ISI(void)
base64_digitbuffer_release(struct Base64_DigitBuffer *dbuf);
#endif
