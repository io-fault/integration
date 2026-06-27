extern inline uint8_t
hash_8(uint8_t state, void *data, size_t length);
extern inline uint16_t
hash_16(uint16_t state, void *data, size_t length);
extern inline uint32_t
hash_32(uint32_t state, void *data, size_t length);
extern inline uint64_t
hash_64(uint64_t state, void *data, size_t length);

extern inline uint8_t
hash_aligned_8(uint8_t state, void *data, size_t length);
extern inline uint16_t
hash_aligned_16(uint16_t state, void *data, size_t length);
extern inline uint32_t
hash_aligned_32(uint32_t state, void *data, size_t length);
extern inline uint64_t
hash_aligned_64(uint64_t state, void *data, size_t length);
