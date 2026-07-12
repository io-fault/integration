#define CACHE_PARAMETERS(F, ...) \
	F(key_size, const size_t, void) \
	F(value_size, const size_t, void) \
	F(identify_data, cache_key_identity_t, void *, size_t) \
	F(key_identify, cache_key_identity_t, cache_key_t *) \
	F(key_compare, int, cache_key_t *, cache_key_t *) \
	F(distribution_index, size_t, cache_storage_t *, cache_key_identity_t) \
	F(evict_record, void, cache_storage_t *, cache_record_t) \
	F(initialize_slot, void, cache_storage_t *, cache_record_t, size_t, size_t)
