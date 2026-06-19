/**
	// Telemetry interfaces and registry for controlling measurement captures.

	// Used by &.harness to aggregate the telemetry control interfaces compiled into DSO's.
*/
#include <stdlib.h>
#include <fault/symbols.h>

struct telemetry_controls {
	void (*identify)(const char *);
	void (*transmit)(void);
	void (*discard)(void);
	void (*enable)(void);
	void (*disable)(void);

	struct telemetry_controls *next;
};

struct telemetry_controls * CONCEAL(telemetry_root) = NULL;

/**
	// Register control interfaces to be invoked by the telemetry APIs.
*/
void
telemetry_register(struct telemetry_controls *ctl)
{
	ctl->next = telemetry_root;
	telemetry_root = ctl;
}

#define foreach(NAME) \
	for (struct telemetry_controls * NAME = telemetry_root; NAME != NULL; NAME = NAME->next)

/**
	// Signal the captures to change the identity (source) of the measurements.
*/
void
telemetry_identify(const char *identity)
{
	setenv("METRICS_IDENTITY", identity, 1);

	foreach(ctl)
		ctl->identify(identity);
}

/**
	// Signal the captures to transmit and discard the collected measurements.
*/
void
telemetry_transmit(void)
{
	foreach(ctl)
		ctl->transmit();
}

/**
	// Signal the captures to discard any collected measurements.
*/
void
telemetry_discard(void)
{
	foreach(ctl)
		ctl->discard();
}

/**
	// Signal the captures to start collecting measurements.
*/
void
telemetry_enable(void)
{
	foreach(ctl)
		ctl->enable();
}

/**
	// Signal the captures to stop collecting measurements.
*/
void
telemetry_disable(void)
{
	foreach(ctl)
		ctl->disable();
}

#undef foreach
