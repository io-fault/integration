/**
	// TTYN.1 Status Frames.
*/
#include <assert.h>
#include <stdio.h>
#include <stdarg.h>
#include <string.h>
#include <setjmp.h>
#include <stdlib.h>
#include <stdbool.h>
#include <unistd.h>
#include <inttypes.h>
#include <wchar.h>
#include <fcntl.h>
#include <errno.h>
#include <sys/uio.h>
#include <sys/types.h>
#include <sys/time.h>
#include <sys/resource.h>

#define _FAULT_STATUS_INTERNAL_
#include <fault/status/requirements.h>
#include <fault/status.h>

const stf_string_t stf_protocol = (stf_string_t) STF_PROTOCOL;
const stf_string_t stf_protocol_ttyn1_declaration = (stf_string_t)
	"[!? PROTOCOL: " STF_PROTOCOL " tty-notation-1]";

#ifndef STF_MALLOC
	#define STF_MALLOC(S) malloc(S)
#endif
#ifndef STF_REALLOC
	#define STF_REALLOC(P, S) realloc(P, S)
#endif
#ifndef STF_FREE
	#define STF_FREE(P) free(P)
#endif

STF_ISI(size_t)
_stf_calculate_type_code(uint8_t *buffer, uint32_t code)
{
	size_t seqlen = 0;

	seqlen += utf8_sequence_codepoint(buffer, code >> 16);
	seqlen += utf8_sequence_codepoint(buffer + seqlen, code & 0xFFFF);
	return(seqlen);
}

/**
	// Get the frame type identifier ("?!") from the given code using
	// a lookup table built from &STF_EVENTS.

	// [ Returns ]
	// The associated type identifier or "??" if unrecognized.
*/
STF_ISI(stf_string_t)
stf_type_identifier(int64_t code)
{
	switch (code)
	{
		#define ET(TID1, TID2, ...) \
			case STF_EVENT_TYPE_CODE(TID1, TID2): \
				return((stf_string_t) TID1 TID2); \
			break;
			STF_EVENTS(ET)
		#undef ET

		default:
		break;
	}

	return((stf_string_t) "??");
}

/**
	// Get the frame type symbol ("elements-inserted") from the given code using
	// a lookup table built from &STF_EVENTS.

	// [ Returns ]
	// The dash separated identifier string associated with the type code or
	// `"unrecognized-frame-type"` if the code is not recognized.
*/
STF_ISI(stf_string_t)
stf_type_symbol(int64_t code)
{
	switch (code)
	{
		#define ET(TID1, TID2, ...) \
			case STF_EVENT_TYPE_CODE(TID1, TID2): \
				return((stf_string_t) STF_EVENT_TYPE_SYMBOL_STRING(__VA_ARGS__)); \
			break;
			STF_EVENTS(ET)
		#undef ET

		default:
		break;
	}

	return((stf_string_t) "unrecognized-frame-type");
}

/**
	// Calculates the additional storage required to integrate the event.
*/
STF_API(size_t)
stf_size_event(struct EStructAllocation *esa, stf_event_parameters)
{
	size_t st_length = 0;

	esa->esa_fields.code = 0;
	esa->esa_string_storage[0] = 0;

	st_length += esa->esa_string_lengths[0] = strlen((const char *) identifier);
	st_length += esa->esa_string_lengths[1] = strlen((const char *) symbol);
	st_length += esa->esa_string_lengths[2] = strlen((const char *) abstract);

	st_length += sizeof(esa->esa_string_lengths) / sizeof(uint16_t); // NULs

	return(st_length);
}

/**
	// Update the EStruct pointers after a memory move to reflect the new positions.

	// &stf_event_t.protocol is expected to be consistent.

	// [ Returns ]
	// Pointer (identical) to &esa as a &stf_event_t.
*/
STF_API(stf_event_t *)
stf_update_storage(struct EStructAllocation *esa)
{
	size_t st_length = sizeof(*esa);
	size_t offsets[3];

	offsets[0] = st_length + 1;
	offsets[1] = offsets[0] + esa->esa_string_lengths[0] + 1;
	offsets[2] = offsets[1] + esa->esa_string_lengths[1] + 1;

	esa->esa_fields.identifier = (stf_string_t) esa + offsets[0];
	esa->esa_fields.symbol = (stf_string_t) esa + offsets[1];
	esa->esa_fields.abstract = (stf_string_t) esa + offsets[2];
}

/**
	// Copy the given event parameters into &esa.

	// [ Returns ]
	// Pointer (identical) to &esa as a &stf_event_t.
*/
STF_API(stf_event_t *)
stf_integrate_event(struct EStructAllocation *esa, stf_event_parameters)
{
	int idx;

	esa->esa_fields.protocol = protocol;
	esa->esa_fields.code = code;

	#define _FSETS(CONTEXT, INDEX, NAME, TYPE) \
		strncpy((char *) esa->esa_fields.NAME, (const char *) NAME, \
			esa->esa_string_lengths[INDEX-3]+1);

		_ESTRUCT_FIELDS_S(_FSETS)
	#undef _FSETS

	return((struct EStruct *) esa);
}

/**
	// Allocate and initialize an &stf_event_t.

	// [ Returns ]
	// Single &STF_MALLOC allocation holding a copy of the given parameters.
*/
STF_API(stf_event_t *)
stf_construct_event(stf_event_parameters)
{
	size_t st_length = sizeof(struct EStructAllocation);
	uint16_t sfsizes[3];
	struct EStructAllocation *ftype;

	st_length += sfsizes[0] = strlen((const char *) identifier);
	st_length += sfsizes[1] = strlen((const char *) symbol);
	st_length += sfsizes[2] = strlen((const char *) abstract);

	st_length += sizeof(sfsizes) / sizeof(uint16_t); // NULs

	ftype = (struct EStructAllocation *) STF_MALLOC(st_length);

	ftype->esa_fields.protocol = protocol;
	ftype->esa_fields.code = code;
	ftype->esa_string_storage[0] = 0;

	ftype->esa_fields.identifier = (stf_string_t)
		ftype + sizeof(struct EStructAllocation) + 1;
	ftype->esa_fields.symbol = (stf_string_t)
		ftype + sizeof(struct EStructAllocation) + 2 + sfsizes[0];
	ftype->esa_fields.abstract = (stf_string_t)
		ftype + sizeof(struct EStructAllocation) + 3 + sfsizes[0] + sfsizes[1];

	// Copy stf_event string arguments.
	#define _FSETS(CONTEXT, INDEX, NAME, TYPE) \
		strcpy((char *) ftype->esa_fields.NAME, (const char *) NAME);

		_ESTRUCT_FIELDS_S(_FSETS)
	#undef _FSETS

	return((struct EStruct *) ftype);
}

/**
	// Compare all of the fields of the two event types.

	// [ Returns ]
	// Zero when the data in all of the fields are identical.
	// Otherwise, the index of the fields that differ.
*/
STF_API(stf_event_field_t)
stf_event_compare(stf_event_t *op1, stf_event_t *op2)
{
	if (op1->protocol != op2->protocol)
		return(stf_event_protocol_fi);
	if (op1->code != op2->code)
		return(stf_event_code_fi);

	#define _FCMP(CONTEXT, INDEX, NAME, TYPE) \
		if (strcmp((const char *) op1->NAME, (const char *) op2->NAME)) \
			return((stf_event_field_t) INDEX);

		_ESTRUCT_FIELDS_S(_FCMP)
	#undef _FCMP

	return(stf_event_void_fi);
}

/**
	// Identify the exact size required to represent the TTYN.1 Status Frame.

	// [ Returns ]
	// Number of bytes required to hold the formatted frame.
*/
STF_API(size_t)
ttyn1_size_frame(stf_string_t channel, stf_string_t type, stf_string_t synopsis, size_t extension_length)
{
	size_t r = extension_length, dcount = 1;

	// Calculate decimal digits for extension size representation.
	#define _count_digits(N, D) \
		while (r >= D) \
		{ \
			r /= D; \
			dcount += N; \
		}
	_count_digits(1000000, 6)
	_count_digits(1000, 3)
	_count_digits(10, 1)
	#undef _count_digits

	return(
		1 + // "["
		strlen((const char *) type) +
		1 + // " "
		strlen((const char *) synopsis) +
		2 + // " ("
		strlen((const char *) channel) +
		sizeof(TTYN1_OPEN_URL) - 1 +
		sizeof(TTYN1_DATA_URL) - 1 +
		base64_encoded_size(extension_length) +
		sizeof(TTYN1_CLOSE_URL) - 1 +
		1 + // "+" signal
		(size_t) dcount,
		sizeof(TTYN1_RESET_URL) - 1 +
		sizeof(TTYN1_SIGNATURE) - 1 +
		3 // ")]\n"
	);
}

/**
	// Format the metrics into &buffer.
	// Generally presumes &length is sufficient, but will return negative
	// on &snprintf failures.

	// [ Parameters ]
	// /buffer/
		// Memory area to format the metrics string into.
	// /length/
		// Size of the buffer.
	// /psm/
		// The metrics to be formatted as a string.

	// [ Returns ]
	// Total number of bytes written into &buffer or a negative value
	// returned by &snprintf.
*/
STF_API(int)
stf_sequence_metrics(char *buffer, size_t length, stf_metrics_t *psm)
{
	int r, total = 0;
	char *p = buffer;

	// All zeros is empty string.
	*buffer = 0;

	if (stf_work_zeros(psm->ps_work) < sizeof(psm->ps_work) / sizeof(stf_count_t))
	{
		r = snprintf(p, length,
			"%" STF_WORK_CODE stf_work_format(STF_COUNT_FMT),
			stf_work_arguments(psm->ps_work)
		);
		if (r < 0)
			return(r);
	}
	else
		r = 0;

	total += r;
	p += r;
	length -= r;

	if (stf_advisory_zeros(psm->ps_message) < sizeof(psm->ps_message) / sizeof(stf_count_t))
	{
		r = snprintf(p, length,
			"%s" STF_ADVISORY_CODE stf_advisory_format(STF_COUNT_FMT),
			total > 0 ? " " : "",
			stf_advisory_arguments(psm->ps_message)
		);
		if (r < 0)
			return(r);
	}
	else
		r = 0;

	total += r;
	p += r;
	length -= r;

	if (stf_resource_zeros(psm->ps_usage) < sizeof(psm->ps_usage) / sizeof(stf_count_t))
	{
		r = snprintf(p, length,
			"%s" STF_RESOURCE_CODE stf_resource_format(STF_COUNT_FMT),
			total > 0 ? " " : "",
			stf_resource_arguments(psm->ps_usage)
		);
		if (r < 0)
			return(r);
	}
	else
		r = 0;

	return(total + r);
}

/**
	// Scan the &source for the field codes and fill &psm with
	// the corresponding values. Each section in &stf_metrics_t
	// is optional, but the order of the sets should be consistent
	// with the order in the string.

	// [ Parameters ]
	// /psm/
		// The metrics structure to fill.
	// /source/
		// The NUL-terminated string containing the field codes
		// with adjacent decimal values.

	// [ Returns ]
	// Number of sections (work, advisory, resource) found and scanned.
*/
STF_API(int)
stf_structure_metrics(stf_metrics_t *psm, const char *source)
{
	int r, t = 0;
	const char *p;

	p = strstr(source, "%");
	if (p != NULL)
	{
		r = sscanf(p+1,
			stf_work_format(STF_COUNT_FMT),
			stf_work_arguments(& psm->ps_work)
		);
		t += 1;

		p = strstr(p, "@");
	}
	else
	{
		psm->ps_work.w_executed = 0;
		psm->ps_work.w_failed = 0;
		psm->ps_work.w_granted = 0;
		psm->ps_work.w_prepared = 0;

		p = strstr(source, "@");
	}

	if (p != NULL)
	{
		r = sscanf(p+1,
			stf_advisory_format(STF_COUNT_FMT),
			stf_advisory_arguments(& psm->ps_message)
		);
		t += 1;

		p = strstr(p, "$");
	}
	else
	{
		psm->ps_message.m_notices = 0;
		psm->ps_message.m_warnings = 0;
		psm->ps_message.m_errors = 0;

		p = strstr(source, "$");
	}

	if (p != NULL)
	{
		r = sscanf(p+1,
			stf_resource_format(STF_COUNT_FMT),
			stf_resource_arguments(& psm->ps_usage)
		);

		t += 1;
	}
	else
	{
		psm->ps_usage.r_process = 0;
		psm->ps_usage.r_time = 0;
		psm->ps_usage.r_memory = 0;
		psm->ps_usage.r_divisions = 0;
	}

	return(t);
}

/**
	// Increase the indentation level of &txt by inserting &level count of
	// `'\t'` bytes after all `'\n'` bytes found in &txt.

	// Empty lines are not indented.

	// [ Parameters ]
	// /out/
		// Pointer to write the new allocation's address to.
	// /txt/
		// The text to copy that will have tabs inserted after newlines.
	// /length/
		// The length of the &txt; NUL characters are treated as regular
		// characters.
	// /estimate/
		// The presumed number of lines in &txt. If the exact number is known,
		// no reallocations should be necessary.
	// /level/
		// The number of tabs to insert.

	// [ Returns ]
	// Exact number of bytes written in &out.
	// The allocation size, of &out, may exceed this by some multiple of &level.
*/
STF_API(size_t)
stf_indent_text(uint8_t **out, stf_string_t txt, size_t length, uint16_t estimate, uint8_t level)
{
	size_t txtlen = length, count = 0;
	char *x = (char *) txt, *y;
	char *rs;
	size_t bufpos = 0, buflen = length + (estimate * level);

	// Estimate.
	rs = (char *) STF_MALLOC(buflen);
	if (rs == NULL)
	{
		*out = NULL;
		return(0);
	}

	if (txtlen > 0 && *x != '\n')
	{
		for (int i = 0; i < level; ++i)
			(rs + bufpos)[i] = '\t';
		bufpos += level;
	}

	while (y = (char *) memchr(x, (int) '\n', txtlen))
	{
		size_t d = ((intptr_t) y - (intptr_t) x);
		assert(txtlen >= d + 1);

		if (bufpos + d + level + 1 > buflen)
		{
			// There's enough for the entire content of &txt,
			// so this is only compensating for newlines beyond
			// the estimate.
			buflen += level * 8;
			rs = (char *) STF_REALLOC(rs, buflen);
			if (rs == NULL)
			{
				*out = NULL;
				return(0);
			}
		}

		assert((x + d)[0] == '\n');
		memcpy(rs + bufpos, x, d+1);
		bufpos += d + 1;

		// Advance search position beyond the identified newline.
		txtlen -= d + 1;
		x = y + 1;

		// Insert indentations; reallocation should guarantee available space.
		// Only indent lines with content.
		if (txtlen > 0 && *x != '\n')
		{
			for (int i = 0; i < level; ++i)
				(rs + bufpos)[i] = '\t';
			bufpos += level;
		}
	}

	// Remaining data in &txt without a trailing newline.
	memcpy(rs + bufpos, x, txtlen);

	*out = (uint8_t *) rs;
	return(bufpos + txtlen);
}

static void
_ttyn1_copy_encoded(void *context, uint8_t *data, size_t length)
{
	struct iovec *buffer = (struct iovec *) context;

	// Zero length copies when buffer is full,
	// ttyn1_format_frame will check buffer status and report failure.
	if (length > buffer->iov_len)
		length = buffer->iov_len;

	memcpy(buffer->iov_base, data, length);
	buffer->iov_base = (void *) (((intptr_t) (buffer->iov_base)) + length);
	buffer->iov_len -= length;
}

STF_API(int)
_ttyn1_format_frame(uint8_t *buffer, size_t length,
	stf_string_t channel, stf_string_t type,
	stf_string_t synopsis, va_list sfp,
	struct iovec *context, struct iovec *application)
{
	int r = 0;
	size_t t = 0, ext_total = 0;
	uint8_t state[4] = {0,};
	struct iovec buf = {buffer, length};

	// TTYN_LOG macros modify the synopsis to include frame formatting.
	r = vsnprintf((char *)buf.iov_base, buf.iov_len, (const char *) synopsis, sfp);
	if (r < 0)
		return(r);
	t += r;
	buf.iov_len -= r;
	buf.iov_base = (void *) (((intptr_t) (buf.iov_base)) + r);

	// Base64 encode the extensions.
	ext_total += base64_transfer_encoded_v(state, _ttyn1_copy_encoded, (void *) &buf, context);
	ext_total += base64_transfer_encoded_v(state, _ttyn1_copy_encoded, (void *) &buf, application);

	// Finish the base64 encoded data when remainder is non-zero.
	if (state[0])
		t += base64_transfer_encoded_v(state, _ttyn1_copy_encoded, (void *) &buf,
			(struct iovec[2]) {(struct iovec){state, 0}, (struct iovec){NULL, 0}}
		);
	t += ext_total;

	// Final snprintf serves as error checking for the previous calls as well.
	r = snprintf((char *) buf.iov_base, buf.iov_len,
		"%s"  // Close URL
		"+"   // Signal
		"%lu" // Data extension size
		"%s"  // Reset + Signature
		")]\n",

		TTYN1_CLOSE_URL,
		base64_decoded_size(ext_total) + state[0],
		TTYN1_RESET_URL
		TTYN1_SIGNATURE
	);
	if (r < 0)
		return(r);

	return(r + t);
}

STF_API(int)
_ttyn1_format_message(uint8_t *buffer, size_t length, ttyn1_message_parameters, ...)
{
	int r;
	size_t synblength;
	va_list sfp;

	va_start(sfp, synopsis);

	r = _ttyn1_format_frame(buffer, length, channel, type, synopsis,
		sfp, TTYN_EXTENSION(
			TTYN_INSERT_OPTION("@transaction", xid),
			_TTYN_INSERT_TIMESTAMP
		), ext
	);

	va_end(sfp);

	return(r);
}

STF_API(int)
_ttyn1_format_transaction(uint8_t *buffer, size_t length, ttyn1_transaction_parameters, ...)
{
	int r;
	char msb[TTYN_MAX_METRICS];
	uint8_t *metrics;
	size_t mlength;
	va_list sfp;

	// @metrics
	if (psm != NULL)
	{
		mlength = stf_sequence_metrics(msb, sizeof(msb), psm);
		metrics = (uint8_t *) msb;
	}
	else
	{
		mlength = 0;
		metrics = (uint8_t *) NULL;
	}

	va_start(sfp, synopsis);
	r = _ttyn1_format_frame(buffer, length, channel, type, synopsis,
		sfp, TTYN_EXTENSION(
			TTYN_INSERT_OPTION("@transaction", xid),
			_TTYN_INSERT_TIMESTAMP,
			TTYN_INSERT_SIZED_OPTION("@metrics", mlength, metrics)
		), ext
	);
	va_end(sfp);

	return(r);
}

static void
_ttyn1_write_encoded(void *context, uint8_t *data, size_t length)
{
	int fd = (intptr_t) context;
	write(fd, data, length);
}

/**
	// Log a TTYN.1 status frame.

	// [ Returns ]
	// Number of bytes written.
*/
STF_API(int)
_ttyn1_log_frame(int fd, stf_string_t channel, stf_string_t type, stf_string_t synopsis, va_list sfp,
	struct iovec *context, struct iovec *application)
{
	int r = 0;
	size_t t = 0, ext_total = 0;
	uint8_t state[4] = {0,};

	// TTYN_LOG macros modify the synopsis to include frame formatting.
	r = vdprintf(fd, (const char *) synopsis, sfp);
	if (r < 0)
		return(r);
	t += r;

	// Base64 encode the extensions.
	ext_total += base64_transfer_encoded_v(state, _ttyn1_write_encoded, (void *) fd, context);
	ext_total += base64_transfer_encoded_v(state, _ttyn1_write_encoded, (void *) fd, application);

	// Finish the base64 encoded data when remainder is non-zero.
	if (state[0])
		t += base64_transfer_encoded_v(state, _ttyn1_write_encoded, (void *) fd,
			(struct iovec[2]) {(struct iovec){state, 0}, (struct iovec){NULL, 0}}
		);
	t += ext_total;

	r = dprintf(fd,
		"%s"  // Close URL
		"+"   // Signal
		"%lu" // Data extension size
		"%s"  // Reset + Signature
		")]\n",

		TTYN1_CLOSE_URL,
		base64_decoded_size(ext_total) + state[0],
		TTYN1_RESET_URL
		TTYN1_SIGNATURE
	);
	if (r < 0)
		return(r);

	return(r + t);
}

STF_API(int)
_ttyn1_log_transaction(int fd, ttyn1_transaction_parameters, ...)
{
	int r;
	char msb[TTYN_MAX_METRICS];
	uint8_t *metrics;
	size_t mlength;
	va_list sfp;

	// @metrics
	if (psm != NULL)
	{
		mlength = stf_sequence_metrics(msb, sizeof(msb), psm);
		metrics = (uint8_t *) msb;
	}
	else
	{
		mlength = 0;
		metrics = (uint8_t *) NULL;
	}

	va_start(sfp, synopsis);
	r = _ttyn1_log_frame(fd, channel, type, synopsis, sfp,
		TTYN_EXTENSION(
			TTYN_INSERT_OPTION("@transaction", xid),
			_TTYN_INSERT_TIMESTAMP,
			TTYN_INSERT_SIZED_OPTION("@metrics", mlength, metrics)
		),
		ext
	);
	va_end(sfp);

	return(r);
}

STF_API(int)
_ttyn1_log_message(int fd, ttyn1_message_parameters, ...)
{
	int r;
	size_t synblength;
	va_list sfp;

	va_start(sfp, synopsis);
	r = _ttyn1_log_frame(fd, channel, type, synopsis,
		sfp, TTYN_EXTENSION(
			TTYN_INSERT_OPTION("@transaction", xid),
			_TTYN_INSERT_TIMESTAMP
		), ext
	);
	va_end(sfp);

	return(r);
}
