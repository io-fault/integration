UTF8_API(const char *)
utf8_error_identifier(enum UTF8Error errid);

UTF8_API(const char *)
utf8_error_message(enum UTF8Error errid);

UTF8_API(bool)
utf8_continuation(uint8_t c);

UTF8_API(uint8_t)
utf8_continuation_value(uint8_t c);

UTF8_API(uint8_t)
utf8_sequence_value(uint8_t c, size_t seq_length);

UTF8_API(size_t)
utf8_identify_sequence_length(uint8_t c);

UTF8_API(bool)
utf8_range_valid(size_t length, uint32_t value);

UTF8_API(size_t)
utf8_identify_codepoint(uint32_t *cp, uint8_t *cv, size_t limit);

UTF8_API(utf8_error_t)
utf8_error_construct(enum UTF8Error code, uint8_t index, uint8_t *cv, size_t length, size_t limit);

UTF8_API(utf8_error_t)
utf8_identify_error(uint8_t *cv, size_t limit);

UTF8_API(utf8_error_t)
utf8_error(uint8_t *cv, size_t limit, size_t length, uint32_t cp);

UTF8_API(size_t)
utf8_sequence_length(uint32_t cp);

UTF8_API(size_t)
utf8_sequence_codepoint(uint8_t *cv, uint32_t cp);

UTF8_ISI(size_t)
utf8_sequence_codepoint_1(uint8_t *cv, uint32_t cp);

UTF8_ISI(size_t)
utf8_sequence_codepoint_2(uint8_t *cv, uint32_t cp);

UTF8_ISI(size_t)
utf8_sequence_codepoint_3(uint8_t *cv, uint32_t cp);

UTF8_ISI(size_t)
utf8_sequence_codepoint_4(uint8_t *cv, uint32_t cp);
