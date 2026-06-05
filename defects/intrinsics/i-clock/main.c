/**
	// Validate clock view functions and cycle detection.
*/
#include <stdint.h>
#include <unistd.h>
#include <time.h>
#include <fault/libc.h>
#include <fault/clock.h>
#include <fault/test.h>

Test(clock_precision)
{
	clock_view_t cv, *rv;

	rv = clock_view_configure_precision(&cv, 9);
	test->equality(&cv, rv);
	test->equality(_CLOCK_PRECISION, cv.c_precision);
	test->equality(1, cv.c_reduction);
	test->equality(9, clock_view_precision(rv));

	rv = clock_view_configure_precision(&cv, 0);
	test->equality(&cv, rv);
	test->equality(1, cv.c_precision);
	test->equality(_CLOCK_PRECISION, cv.c_reduction);
	test->equality(0, clock_view_precision(rv));
}

Test(clock_cycle)
{
	clock_view_t cv;
	clock_view_t *rv;

	rv = clock_view_configure_cycle(&cv, clock_system_epoch_seconds());
	test->equality(&cv, rv);
	test->equality(2000, cv.c_datum);
	test->equality(5, cv.c_index);
	test->equality(_CLOCK_CYCLE_OFFSET_DAYS, cv.c_days);
}

// Mostly sanity.
Test(y2k1_nanoseconds)
{
	uint64_t t1, t2, d1;

	d1 = clock_view_elapsed(&y2k1_ns_clock);
	t1 = clock_view_time(&y2k1_ns_clock);

	t2 = clock_view_translate_u(&epoch_ns_clock, &y2k1_ns_clock, t1);
	test->equality(_CLOCK_OFFSET, (t1 - t2) / _CLOCK_PRECISION);

	test->equality(1, clock_view_datum_offset(&y2k1_ns_clock));
}

// Mostly sanity.
Test(y2k1_microseconds)
{
	uint64_t t1, t2, d1;

	d1 = clock_view_elapsed(&y2k1_us_clock);
	t1 = clock_view_time(&y2k1_us_clock);

	t2 = clock_view_translate_u(&epoch_ns_clock, &y2k1_us_clock, t1);
	t1 *= 1000;
	test->equality(_CLOCK_OFFSET, (t1 - t2) / _CLOCK_PRECISION);

	test->equality(1, clock_view_datum_offset(&y2k1_us_clock));
}

/**
	// Check epoch's large datum offset.
*/
Test(view_datum_offset)
{
	const int64_t y2k = _CLOCK_DAYS_IN_CYCLE * 5;
	const int64_t epochd = _CLOCK_DAYS_IN_CYCLE * 4;

	test->equality(y2k - _CLOCK_CYCLE_OFFSET_DAYS - epochd, clock_view_datum_offset(&epoch_ns_clock));
}

Test(translate_smaller_precision)
{
	int64_t t1 = 0, t2;

	t1 = 0;
	t2 = clock_view_translate_s(&y2k1_us_clock, &y2k1_ns_clock, t1);
	test->equality(0, t2);

	t1 = 1000;
	t2 = clock_view_translate_s(&y2k1_us_clock, &y2k1_ns_clock, t1);
	test->equality(1, t2);

	t1 = 2000;
	t2 = clock_view_translate_s(&y2k1_us_clock, &y2k1_ns_clock, t1);
	test->equality(2, t2);

	t1 = -1000;
	t2 = clock_view_translate_s(&y2k1_us_clock, &y2k1_ns_clock, t1);
	test->equality(-1, t2);
}

Test(translate_larger_precision)
{
	int64_t t1 = 0, t2;

	t1 = 0;
	t2 = clock_view_translate_s(&y2k1_ns_clock, &y2k1_us_clock, t1);
	test->equality(0, t2);

	t1 = 1;
	t2 = clock_view_translate_s(&y2k1_ns_clock, &y2k1_us_clock, t1);
	test->equality(1000, t2);

	t1 = 2;
	t2 = clock_view_translate_s(&y2k1_ns_clock, &y2k1_us_clock, t1);
	test->equality(2000, t2);

	t1 = -1;
	t2 = clock_view_translate_s(&y2k1_ns_clock, &y2k1_us_clock, t1);
	test->equality(-1000, t2);
}

Test(translate_equal_precision)
{
	int64_t t1 = 0, t2;

	t1 = 0;
	t2 = clock_view_translate_s(&y2k1_us_clock, &y2k1_us_clock, t1);
	test->equality(0, t2);

	t1 = 1000;
	t2 = clock_view_translate_s(&y2k1_us_clock, &y2k1_us_clock, t1);
	test->equality(1000, t2);

	t1 = 2000;
	t2 = clock_view_translate_s(&y2k1_us_clock, &y2k1_us_clock, t1);
	test->equality(2000, t2);

	t1 = -1000;
	t2 = clock_view_translate_s(&y2k1_us_clock, &y2k1_us_clock, t1);
	test->equality(-1000, t2);
}
