/**
	// Monotonic and real time clock access.

	// This (real time) clock abstraction serves the purpose of adjusting readings
	// to be relative to a configured datum with a configured precision limited
	// to that made available by the system.

	// The &clock_view_t provides the necessary information to translate UNIX
	// epoch timestamps with some desired precision and to publish the datum
	// needed by other programs for interpreting the integer representations.

	// The default, constant, clocks defined by the header provide Y2K+1 datums
	// with microcsecond and nanosecond precision. The extra day is added to the start
	// of the gregorian cycle in order to align the day with the beginning of the week.

	// [ Usage ]

	// Standard headers needed for compilation.
	// #!syntax/c
		#include <stdint.h>
		#include <inttypes.h>
		#include <sys/time.h>
		#include <fault/clock.h>

	// Single integer clock status is the primary purpose:
	// #!syntax/c
		#include <stdio.h>
		int
		main(int argc, char **argv)
		{
			printf("Epoch Nanoseconds: %"  clock_utime_fc "\n", clock_view_time(&epoch_ns_clock));
			printf("Y2K+1 Nanoseconds: %"  clock_utime_fc "\n", clock_view_time(&y2k1_ns_clock));
			printf("Y2K+1 Microseconds: %" clock_utime_fc "\n", clock_view_time(&y2k1_us_clock));
		}

	// Precision and datum translation is included in case epoch relative
	// timestamps are needed.

	// #!syntax/c
		void
		function(void)
		{
			int64_t ts = clock_view_time(&y2k1_us_clock);

			// translated = clock_view_translate(dst, src, original);
			int64_t ets = clock_view_translate(&epoch_ns_clock, &y2k1_us_clock, ts);

			// Expects seconds since epoch.
			foreign_api(ets / epoch_ns_clock.c_precision);
		}
*/
#ifndef _FAULT_CLOCK_H_
#define _FAULT_CLOCK_H_

/**
	// Formatting Codes for signed and unsigned types.
*/
#define clock_utime_fc PRIu64
#define clock_stime_fc PRId64

#ifndef _CLOCK_MONOTONIC
	#if defined(__APPLE__) && defined(CLOCK_MONOTONIC_RAW)
		// Nanosecond precision.
		#define _CLOCK_MONOTONIC CLOCK_MONOTONIC_RAW
	#else
		#define _CLOCK_MONOTONIC CLOCK_MONOTONIC
	#endif
#endif

#ifndef _CLOCK_REAL
	#define _CLOCK_REAL CLOCK_REALTIME
#endif

// Nanoseconds.
#define _CLOCK_PRECISION 1000000000
// Days from 1970 to 2000.
#define _CLOCK_CYCLE_OFFSET_DAYS 10957
// Days in a gregorian cycle.
#define _CLOCK_DAYS_IN_CYCLE 146097

// Y2K+1 offsets.
#define _CLOCK_OFFSET_DAYS (_CLOCK_CYCLE_OFFSET_DAYS + 1)
#define _CLOCK_OFFSET (_CLOCK_OFFSET_DAYS * 24 * 60 * 60)

struct Clock {
	// Datum identity.
	uint16_t c_index;
	uint32_t c_datum;

	// Datum translation support.
	int32_t c_days;
	int64_t c_seconds;

	// Precision scaling.
	uint64_t c_precision;
	uint32_t c_reduction; // Cached for nanosecond scaling.
};

/**
	// Clock structure describing the time context and providing
	// offsets for translating system clock timestamps to be
	// relative to the clock's datum.

	// Initialized by &clock_view_configure_cycle and &clock_view_configure_precision.

	// [ Elements ]
	// /c_index/
		// The gregorian cycle index relative to year zero.
	// /c_datum/
		// The year of the cycle. Usually `2000`.
	// /c_days/
		// The difference of days from the system clock's date.
	// /c_seconds/
		// The difference of seconds from the system clock's date.
		// Used to translate system clock readings.

	// /c_precision/
		// Multiple applied to seconds for scaling to the configured precision.
	// /c_reduction/
		// Reciprocal of the multiple applied to nanoseconds.
*/
typedef struct Clock clock_view_t;

/**
	// Nanosecond precision clock view with Y2K+1 deltas.

	// Provides just over five hundred years of nanosecond
	// readings relative to a cycle with `uint64_t`.
*/
const static clock_view_t y2k1_ns_clock = {
	5, 2000,
	_CLOCK_OFFSET_DAYS,
	_CLOCK_OFFSET,
	_CLOCK_PRECISION, 1
};

/**
	// Microsecond precision clock view with Y2K+1 deltas.

	// Gives reasonable precision while making references to the
	// distant past possible with `int64_t` casts.
*/
const static clock_view_t y2k1_us_clock = {
	5, 2000,
	_CLOCK_OFFSET_DAYS,
	_CLOCK_OFFSET,
	_CLOCK_PRECISION / 1000, 1000
};

/**
	// Nanosecond and microsecond precision clock view for UNIX epoch.

	// Provided for translating timestamps to and from the Y2K clocks.
*/
const static clock_view_t epoch_ns_clock = {
	4, 1970, 0, 0, _CLOCK_PRECISION, 1
};
const static clock_view_t epoch_us_clock = {
	4, 1970, 0, 0, _CLOCK_PRECISION / 1000, 1000
};

/**
	// Retrieve the system's real time clock status in
	// seconds since UNIX epoch.

	// Provided to support &clock_view_configure_cycle.
*/
static inline uint64_t
clock_system_epoch_seconds(void)
{
	struct timespec ts;
	clock_gettime(_CLOCK_REAL, &ts);
	return(ts.tv_sec);
}

/**
	// Identify the nearest, preceding, absolute cycle, year datum, and clock offset
	// using the given epoch &seconds timestamp.

	// Only used when the datum needs to be identified at runtime. Normally,
	// &y2k1_us_clock or &y2k1_ns_clock should be used directly as runtime
	// identification of the datum is not likely to be necessary in practice.

	// [ Parameters ]
	// /cv/
		// The clock to adjust.
	// /seconds/
		// The UNIX epoch relative timestamp to use to configure the clock by.
*/
static clock_view_t *
clock_view_configure_cycle(clock_view_t *cv, int64_t seconds)
{
	int64_t date, days;

	date = seconds / 60 / 60 / 24;

	// Translate to Y2K and make absolute by adding Y2K in.
	days = (date + _CLOCK_CYCLE_OFFSET_DAYS) + (_CLOCK_DAYS_IN_CYCLE * (2000 / 400));

	cv->c_index = days / _CLOCK_DAYS_IN_CYCLE;
	cv->c_datum = cv->c_index * 400;
	cv->c_days = (days - (cv->c_index * _CLOCK_DAYS_IN_CYCLE)) - date;
	cv->c_seconds = cv->c_days * 24 * 60 * 60;

	return(cv);
}

/**
	// Configure the precision of clock readings.
	// This is always subject to the limits of the system clock.

	// [ Parameters ]
	// /cv/
		// The clock to configure.
	// /power/
		// The negative power of ten selecting the precision to be
		// returned by clock readings. `9` for nanoseconds, `6` for
		// microseconds, and `3` for milliseconds.

		// Positive powers are not supported.
*/
static clock_view_t *
clock_view_configure_precision(clock_view_t *cv, uint8_t power)
{
	uint64_t p = 1;

	// Calculate the exact multiple to use.
	while (power--)
		p = p * 10;

	cv->c_precision = p;

	// Translation multiple for interpreting clock_gettime's nanoseconds.
	cv->c_reduction = _CLOCK_PRECISION / p;

	return(cv);
}

/**
	// Calculate the negative power of the clock's precision.
*/
static inline uint8_t
clock_view_precision(clock_view_t *cv)
{
	uint8_t p = 0;
	uint64_t v = cv->c_precision;

	while (v > 1)
	{
		v /= 10;
		++p;
	}

	return(p);
}

/**
	// Calculate the day offset from the datum.
*/
static inline int32_t
clock_view_datum_offset(clock_view_t *cv)
{
	const int64_t y2k = _CLOCK_DAYS_IN_CYCLE * 5;
	const int64_t epoch = y2k - _CLOCK_CYCLE_OFFSET_DAYS;
	int64_t cycle = cv->c_index * _CLOCK_DAYS_IN_CYCLE;

	return((cv->c_days + epoch) - cycle);
}

/**
	// Tranlate the given UNIX epoch relative &seconds and &nanoseconds
	// into a single, &cv datum relative, timestamp integer.

	// [ Parameters ]
	// /cv/
		// The clock whose offsets should be used to translate
		// the &seconds and &nanoseconds.
	// /seconds/
		// Seconds since UNIX epoch.
	// /nanoseconds/
		// Subsecond units to add into the timestamp after precision
		// adjustments.

	// [ Returns ]
	// The &cv relative integer timestamp.
*/
static inline int64_t
clock_view_epoch_s(clock_view_t *cv, int64_t seconds, int64_t nanoseconds)
{
	int64_t i;
	i = (seconds - cv->c_seconds) * cv->c_precision;
	i += nanoseconds / cv->c_reduction;
	return(i);
}

/***/
static inline uint64_t
clock_view_epoch_u(clock_view_t *cv, uint64_t seconds, uint64_t nanoseconds)
{
	uint64_t i;
	i = (seconds - cv->c_seconds) * cv->c_precision;
	i += nanoseconds / cv->c_reduction;
	return(i);
}

/**
	// Read the clock's time using the &clock_gettime system interface
	// with a real time clock.
*/
static inline uint64_t
clock_view_time(clock_view_t *cv)
{
	struct timespec ts;
	clock_gettime(_CLOCK_REAL, &ts);
	return(clock_view_epoch_u(cv, ts.tv_sec, ts.tv_nsec));
}

/**
	// Read the clock's time using the &clock_gettime system interface
	// with a monotonic clock.
*/
static inline uint64_t
clock_view_elapsed(clock_view_t *cv)
{
	uint64_t i;
	struct timespec ts;

	clock_gettime(_CLOCK_MONOTONIC, &ts);
	i = ts.tv_sec * cv->c_precision;
	i += ts.tv_nsec / cv->c_reduction;

	return(i);
}

// Generally requires signed STYPE for proper translation.
#define CLOCK_VIEW_TRANSLATE(STYPE) \
{ \
	STYPE dp = dst->c_precision, sp = src->c_precision; \
	ts += (dst->c_seconds - src->c_seconds) * sp; \
	\
	if (dp >= sp) \
		return(ts * (dp / sp)); \
	else \
		return(ts / (sp / dp)); \
}

/**
	// Tranlate the given &src relative timestamp, &ts, to be
	// relative to the &dst clock.

	// [ Parameters ]
	// /dst/
		// The target clock.
	// /src/
		// The clock of &ts.
	// /ts/
		// The timestamp to convert.

	// [ Returns ]
	// The translated, &dst relative, timestamp with adjusted precision.
*/
static inline uint64_t
clock_view_translate_u(clock_view_t *dst, clock_view_t *src, uint64_t ts)
CLOCK_VIEW_TRANSLATE(int64_t)

/***/
static inline int64_t
clock_view_translate_s(clock_view_t *dst, clock_view_t *src, int64_t ts)
CLOCK_VIEW_TRANSLATE(int64_t)

#endif
