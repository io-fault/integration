STF_API(size_t)
stf_size_event(struct EStructAllocation *esa, stf_event_parameters);

STF_API(stf_event_t *)
stf_update_storage(struct EStructAllocation *esa);

STF_API(stf_event_t *)
stf_integrate_event(struct EStructAllocation *esa, stf_event_parameters);

STF_API(stf_event_t *)
stf_construct_event(stf_event_parameters);

STF_API(stf_event_field_t)
stf_event_compare(stf_event_t *op1, stf_event_t *op2);

STF_API(size_t)
ttyn1_size_frame(stf_string_t channel, stf_string_t type, stf_string_t synopsis, size_t extension_length);

STF_API(int)
stf_sequence_metrics(char *buffer, size_t length, stf_metrics_t *psm);

STF_API(int)
stf_structure_metrics(stf_metrics_t *psm, const char *source);

STF_API(size_t)
stf_indent_text(uint8_t **out, stf_string_t txt, size_t length, uint16_t estimate, uint8_t level);

STF_API(int)
_ttyn1_format_frame(uint8_t *buffer, size_t length,
	stf_string_t channel, stf_string_t type,
	stf_string_t synopsis, va_list sfp,
	struct iovec *context, struct iovec *application);

STF_API(int)
_ttyn1_format_message(uint8_t *buffer, size_t length, ttyn1_message_parameters, ...);

STF_API(int)
_ttyn1_format_transaction(uint8_t *buffer, size_t length, ttyn1_transaction_parameters, ...);

STF_API(int)
_ttyn1_log_frame(int fd, stf_string_t channel, stf_string_t type, stf_string_t synopsis, va_list sfp,
	struct iovec *context, struct iovec *application);

STF_API(int)
_ttyn1_log_transaction(int fd, ttyn1_transaction_parameters, ...);

STF_API(int)
_ttyn1_log_message(int fd, ttyn1_message_parameters, ...);

STF_ISI(size_t)
_stf_calculate_type_code(uint8_t *buffer, uint32_t code);

STF_ISI(stf_string_t)
stf_type_identifier(int64_t code);

STF_ISI(stf_string_t)
stf_type_symbol(int64_t code);
