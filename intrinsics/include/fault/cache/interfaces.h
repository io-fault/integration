#define CACHE_INTERFACES(F, ...) \
	F(default_hash, cache_key_identity_t, void *, size_t) \
	F(initialize, int, cache_storage_t *, size_t, size_t, size_t) \
	F(initialized, bool, cache_storage_t *) \
	F(release, void, cache_storage_t *) \
	F(create, cache_storage_t *, size_t, size_t, size_t) \
	F(destroy, void, cache_storage_t *) \
	F(truncate_distributions, size_t, cache_storage_t *, size_t, size_t) \
	F(truncate_records, size_t, cache_storage_t *) \
	\
	F(record_capacity, size_t, cache_storage_t *) \
	F(record_count, size_t, cache_storage_t *) \
	\
	F(record_initialize, cache_record_t, cache_record_t, cache_key_t *, cache_key_identity_t) \
	F(resize_slots, size_t, cache_storage_t *, size_t, ssize_t) \
	F(acquire_slot, cache_record_t, cache_storage_t *, int, cache_key_t *, cache_key_identity_t) \
	F(acquire_slot_fixed, cache_record_t, cache_storage_t *, int, cache_key_t *, cache_key_identity_t) \
	\
	F(record_size, size_t, void) \
	F(record_key, cache_key_t *, cache_record_t) \
	F(record_value, cache_value_t *, cache_record_t) \
	F(record_set_key, cache_key_t *, cache_record_t, cache_key_t *) \
	F(record_set_value, cache_value_t *, cache_record_t, cache_value_t *) \
	\
	F(insert_record, cache_record_t, cache_storage_t *, cache_key_t *, cache_value_t *) \
	F(select_record, cache_record_t, cache_storage_t *, cache_key_t *) \
	F(delete_record, cache_record_t, cache_storage_t *, cache_key_t *) \
	\
	F(get, cache_value_t *, cache_storage_t *, cache_key_t *) \
	F(set, cache_value_t *, cache_storage_t *, cache_key_t *, cache_value_t *) \
	F(default, cache_value_t *, cache_storage_t *, cache_key_t *, cache_value_t *) \
	F(update, cache_value_t *, cache_storage_t *, cache_key_t *, cache_value_t *) \
	F(delete, cache_value_t *, cache_storage_t *, cache_key_t *) \
	\
	F(require, cache_value_t *, cache_storage_t *, cache_key_t *, cache_slot_f, cache_record_f, void *) \
	F(request, cache_value_t *, cache_storage_t *, cache_key_t *) \
	F(require_record, cache_record_t, cache_storage_t *, cache_key_t *, cache_slot_f, cache_record_f, void *) \
	F(request_record, cache_record_t, cache_storage_t *, cache_key_t *) \
	\
	F(scan_records, size_t, cache_storage_t *, cache_record_f, void *) \
	F(update_records, size_t, cache_storage_t *dst, cache_storage_t *src) \
	F(extend_records, size_t, cache_storage_t *dst, cache_storage_t *src) \
	F(replace_records, size_t, cache_storage_t *dst, cache_storage_t *src) \
	F(discard_records, size_t, cache_storage_t *dst, cache_storage_t *src) \
	F(redistribute_records, int, cache_storage_t *, size_t)
