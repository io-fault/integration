/**
	# C structures and macros for performing tests at the C-level.
*/

/**
	# Test fate enumeration.
*/
enum test_fate_t {
	tf_executing = -1,

	tf_pass = 0,
	tf_return = 1,

	tf_explicit,
	tf_skip,
	tf_divide,
	tf_absurdity,
	tf_fail,
	tf_void,
	tf_expire,
	tf_interrupt,
	tf_core
}
typedef enum test_fate_t test_fate_t;

/**
	# Test information structure.
*/
struct Test {
	unsigned long test_checks;
	test_fate_t test_fate;
	const char *test_fate_description;
	const char *operands[2];
}

#define test_equality(T,A,B) do { \
	T->test_checks += 1; \
	if (A!=B) { \
		T->test_fate = tf_absurdity;
		T->operands[0] = #A;
		T->operands[1] = #B;
	} \
} while(0)

#define test_fail(T, string) T->test_fate_description = string
