/**
	// Storage hash implementations.

	// Currently, a trivial implementation serving as a functional placeholder.

	// The aligned versions only hash up to multiples of the hash size.
*/
#include <stdint.h>
#include <stdlib.h>
#include <sys/types.h>
#include <string.h>

#if __INCLUDE_LEVEL__ == 0
	#define FAULT_METRICS_LINKED
	#include <fault/metrics.h>
#endif

/*
	// Multiplication and xor mixing with a special case for zeros.
*/
#define HASH(FINAL, TYPE, INIT, FACTOR, DATA, LENGTH) \
	TYPE h = (TYPE) INIT; \
	TYPE *uv = (TYPE *) DATA; \
	TYPE s = 0; \
	size_t units = LENGTH / sizeof(TYPE); \
	size_t r = LENGTH - (units * sizeof(TYPE)); \
	int i = 0; \
	\
	for (size_t i = 0; i < units; ++i) \
	{ \
		if (uv[i] == 0) \
		{ \
			++s; \
			h ^= (s * FACTOR); \
		} \
		else \
			h ^= (uv[i] * FACTOR); \
	} \
	FINAL(TYPE, INIT, FACTOR, DATA, LENGTH)

/* Used by aligned variants. */
#define IGNORE(TYPE, INIT, FACTOR, DATA, LENGTH) return(h);

/* Copy remaining bytes over a zero and hash. */
#define FINISH(TYPE, INIT, FACTOR, DATA, LENGTH) \
	if (r > 0) \
	{ \
		TYPE p = 0; \
		memcpy(&p, DATA + (LENGTH - r), r); \
		if (p == 0) \
		{ \
			++s; \
			h ^= (s * FACTOR); \
		} \
		else \
			h ^= (p * FACTOR); \
	} \
	return(h);

/**
	// Hash &length bytes of &data starting with &state.
	// - &hash_8
	// - &hash_16
	// - &hash_32
	// - &hash_64

	// [ Parameters ]
	// /state/
		// The starting hash value. Any number can be given.
	// /data/
		// The data to be identified.
	// /length/
		// The number of bytes in &data to process.

	// [ Returns ]
	// Unsigned value consistent with the bit length identified by
	// the selected hash function.
*/
static unsigned int
hash(unsigned int state, void *data, size_t length)
{
	// Documentation point for the hash implementations.
	return(state);
}

/**
	// Hash &length bytes of &data starting with &state, but only
	// up to a multiple of the hash's size.

	// - &hash_aligned_8
	// - &hash_aligned_16
	// - &hash_aligned_32
	// - &hash_aligned_64

	// [ Parameters ]
	// /state/
		// The starting hash value. Any number can be given.
	// /data/
		// The data to be identified.
	// /length/
		// The number of bytes in &data to process.
		// Length beyond the last whole multiple of the hash size will be ignored.

	// [ Returns ]
	// Unsigned value consistent with the bit length identified by
	// the selected hash function.
*/
static unsigned int
hash_aligned(unsigned int state, void *data, size_t length)
{
	// Documentation point for the aligned hash implementations.
	return(state);
}

/* Function body templates for direct identities. */

extern inline uint8_t
hash_8(uint8_t state, void *data, size_t length)
{
	HASH(IGNORE, uint8_t, state, 0x1F, data, length)
}

extern inline uint16_t
hash_16(uint16_t state, void *data, size_t length)
{
	HASH(FINISH, uint16_t, state, 0x1F2E, data, length)
}

extern inline uint32_t
hash_32(uint32_t state, void *data, size_t length)
{
	HASH(FINISH, uint32_t, state, 0x1F2E3D4C, data, length)
}

extern inline uint64_t
hash_64(uint64_t state, void *data, size_t length)
{
	HASH(FINISH, uint64_t, state, 0x1F2E3D4C5B6A7988, data, length)
}

extern inline uint8_t
hash_aligned_8(uint8_t state, void *data, size_t length)
{
	HASH(IGNORE, uint8_t, state, 0x1F, data, length)
}

extern inline uint16_t
hash_aligned_16(uint16_t state, void *data, size_t length)
{
	HASH(IGNORE, uint16_t, state, 0x1F2E, data, length)
}

extern inline uint32_t
hash_aligned_32(uint32_t state, void *data, size_t length)
{
	HASH(IGNORE, uint32_t, state, 0x1F2E3D4C, data, length)
}

extern inline uint64_t
hash_aligned_64(uint64_t state, void *data, size_t length)
{
	HASH(IGNORE, uint64_t, state, 0x1F2E3D4C5B6A7988, data, length)
}
