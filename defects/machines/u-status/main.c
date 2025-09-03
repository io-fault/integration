/**
	// Validate Status Frame headers.
*/
#include <fault/libc.h>
#include <fault/test.h>
#include <fault/status.h>

/**
	// Validate that the macro is processing the long strings as anticipated.

	// Currently, little endian is presumed.
*/
Test(stf_type_codes)
{
	uint8_t buf[9];
	test->equality(2162751, STF_EVENT_TYPE_CODE("!", "?"));
	test->equality(stf_message_protocol_event, STF_EVENT_TYPE_CODE("!", "?"));
	test->equality(stf_data_received_event, STF_EVENT_TYPE_CODE("↓", ":"));
	test->equality(stf_data_transmitted_event, STF_EVENT_TYPE_CODE("↑", ":"));

	test->strcmp("!?", stf_type_identifier(2162751));
	test->strcmp("↓↑", stf_type_identifier(563290513));
}

/**
	// Identify the UTF-8 representation of an arbitrary type code.
	// (Not using the lookup table to constants)
*/
Test(_stf_calculate_type_code)
{
	uint8_t buf[10];

	buf[_stf_calculate_type_code(buf, STF_EVENT_TYPE_CODE("!", "?"))] = 0;
	test->strcmp("!?", buf);

	buf[_stf_calculate_type_code(buf, STF_EVENT_TYPE_CODE("<", ">"))] = 0;
	test->strcmp("<>", buf);

	buf[_stf_calculate_type_code(buf, STF_EVENT_TYPE_CODE(">", "<"))] = 0;
	test->strcmp("><", buf);

	buf[_stf_calculate_type_code(buf, STF_EVENT_TYPE_CODE("-", ">"))] = 0;
	test->strcmp("->", buf);

	buf[_stf_calculate_type_code(buf, STF_EVENT_TYPE_CODE("<", "-"))] = 0;
	test->strcmp("<-", buf);
}

/**
	// Check &stf_type_symbol' table and unrecognized fallback.
*/
Test(stf_type_symbol_lookup)
{
	#define ET(F, L, ...) \
		test->strcmp(STF_EVENT_TYPE_SYMBOL_STRING(__VA_ARGS__), \
			stf_type_symbol(STF_EVENT_TYPE_CODE(F, L)));
		STF_EVENTS(ET)
	#undef ET

	test->strcmp("unrecognized-frame-type",
		stf_type_symbol(STF_EVENT_TYPE_CODE("X", "Y")));
}

/**
	// Check &stf_type_identifier' table and unrecognized fallback.
*/
Test(stf_type_identifier_lookup)
{
	#define ET(F, L, ...) \
		test->strcmp(F L, stf_type_identifier(STF_EVENT_TYPE_CODE(F, L)));
		STF_EVENTS(ET)
	#undef ET

	test->strcmp("??",
		stf_type_identifier(STF_EVENT_TYPE_CODE("X", "Y")));
}

Test(stf_construct_event)
{
	struct EStruct *es;
	es = stf_construct_event(
		"http://protocol",
		-1,
		"Identifier",
		"SYMBOL",
		"Abstract."
	);

	test->strcmp("http://protocol", es->protocol);
	test->equality(-1, es->code);
	test->strcmp("Identifier", es->identifier);
	test->strcmp("SYMBOL", es->symbol);
	test->strcmp("Abstract.", es->abstract);

	STF_FREE(es);
}

Test(stf_event_initializations)
{
	struct EStructAllocation *esa;
	struct EStruct *es, *ez;
	size_t sz;

	esa = STF_MALLOC(sizeof(*esa));
	sz = stf_size_event(esa,
		"http://protocol",
		-1,
		"Identifier",
		"SYMBOL",
		"Abstract."
	);

	esa = STF_REALLOC(esa, sizeof(*esa) + sz);
	stf_update_storage(esa);
	stf_integrate_event(esa,
		"http://protocol",
		-1,
		"Identifier",
		"SYMBOL",
		"Abstract."
	);

	ez = (stf_event_t *) esa;
	test->strcmp("http://protocol", ez->protocol);
	test->equality(-1, ez->code);
	test->strcmp("Identifier", ez->identifier);
	test->strcmp("SYMBOL", ez->symbol);
	test->strcmp("Abstract.", ez->abstract);

	es = stf_construct_event(
		ez->protocol,
		ez->code,
		ez->identifier,
		ez->symbol,
		ez->abstract
	);

	test->truth(!stf_event_compare(es, ez));
	test->memcmp(es + sizeof(*esa), esa + sizeof(*esa), sz);

	STF_FREE(es);
	STF_FREE(esa);
}

Test(stf_event_compare)
{
	stf_event_t e0, e1, e2;

	e0 = e1 = e2 = (stf_event_t) {
		"protocol", -2,
		"identifier", "symbol",
		"abstract"
	};

	test->equality(0, stf_event_compare(&e1, &e2));

	// String fields.
	#define _CMP_FIELDS(CONTEXT, INDEX, NAME, TYPE) \
		e1.NAME = ""; \
		test->equality(INDEX, stf_event_compare(&e1, &e2)); \
		e1.NAME = e2.NAME; e2.NAME = ""; \
		test->equality(INDEX, stf_event_compare(&e1, &e2)); \
		e2.NAME = e0.NAME; \
		test->equality(INDEX, _ESTRUCT_FIELD_INDEX(NAME));
	_ESTRUCT_FIELDS_S(_CMP_FIELDS)

	#define _CMP_FIELDS(CONTEXT, INDEX, NAME, TYPE) \
		e1.NAME = 0; \
		test->equality(INDEX, stf_event_compare(&e1, &e2)); \
		e1.NAME = e2.NAME; e2.NAME = 0; \
		test->equality(INDEX, stf_event_compare(&e1, &e2)); \
		e2.NAME = e0.NAME; \
		test->equality(INDEX, _ESTRUCT_FIELD_INDEX(NAME));
	_ESTRUCT_FIELDS_I(_CMP_FIELDS)

	#undef _CMP_FIELDS
}

Test(stf_metrics_io)
{
	const char *const sample_strings[] = {
		"%0+1-2/3 @4!5*6 $7:8#9/10",
		"%10+11-12/13 @14!15*16 $17:18#19/20",
		"%1+0-0/0",
		"@0!1*0",
		"$0:0#1/2",
		"", // All zeros.
	};
	stf_metrics_t sample_metrics[] = {
		{
			{0, 1, 2, 3},
			{4, 5, 6},
			{7, 8, 9, 10}
		},
		{
			{10, 11, 12, 13},
			{14, 15, 16},
			{17, 18, 19, 20}
		},

		// Some or all zeros.
		{
			{1, 0, 0, 0},
			{0, 0, 0},
			{0, 0, 0, 0}
		},
		{
			{0, 0, 0, 0},
			{0, 1, 0},
			{0, 0, 0, 0}
		},
		{
			{0, 0, 0, 0},
			{0, 0, 0},
			{0, 0, 1, 2}
		},
		{
			{0, 0, 0, 0},
			{0, 0, 0},
			{0, 0, 0, 0}
		},
	};
	stf_count_t sample_section_count[] = {
		3, 3, 1, 1, 1, 0
	};
	stf_metrics_t mbuf = {{0,}, {0,}, {0,}};
	char sbuf[128];

	for (int i = 0; i < sizeof(sample_strings) / sizeof(char *); ++i)
	{
		const char *mstring = sample_strings[i];
		stf_metrics_t *mstruct = &sample_metrics[i];

		test->equality(strlen(mstring), stf_sequence_metrics(sbuf, sizeof(sbuf), mstruct));
		test->strcmp(mstring, sbuf);

		test->equality(sample_section_count[i], stf_structure_metrics(&mbuf, sbuf));
		test->memcmp(&mbuf, mstruct, sizeof(mbuf));
	}
}
