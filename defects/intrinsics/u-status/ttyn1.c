/**
	// Validate Status Frame TTYN.1 Interfaces.
*/
#include <fault/libc.h>

#define TEST_SUITE_EXTENSION
#include <fault/test.h>
#include <fault/status.h>

Test(ttyn1_format_declaration)
{
	uint8_t buf[1024*4];
	size_t len = sizeof(buf)-1;
	int r;

	r = ttyn1_format_declaration(buf, len, NULL, "sample-xid",
		TTYN_INSERT_SECTION("key", "value")
	);
	test(r > 0);
	test->strstr(buf, "http://fault.io/protocol/status/frames");
	test->strstr(buf, "tty-notation-1");
}

#define message_format(SEV, UC, ...) \
	Test(ttyn1_format_##SEV) \
	{ \
		uint8_t buf[1024*4]; \
		size_t len = sizeof(buf)-1; \
		int r; \
		\
		r = ttyn1_format_##SEV(buf, len, NULL, "sample-xid", __VA_ARGS__ __VA_OPT__(,) \
			TTYN_SYNOPSIS("synopsis %s, %s", "formatted", #SEV), \
			TTYN_EXTENSION( \
				TTYN_INSERT_SECTION("key", "value") \
			) \
		); \
		test(r > 0); \
		test->strstr(buf, UC); \
		test->strstr(buf, "synopsis formatted, " #SEV); \
		test->strstr(buf, "data:"); \
		test->strstr(buf, "base64,"); \
		if (strcmp(UC, "TRACE") == 0) \
			test->strstr(buf, "[!~"); \
		else \
			test->strstr(buf, "[!#"); \
	}

message_format(error, "ERROR")
message_format(warning, "WARNING")
message_format(notice, "NOTICE")
message_format(trace, "TRACE", "TRACE")

#define transaction_format(XTYPE, FTYPE) \
	Test(ttyn1_format_##XTYPE##_transaction) \
	{ \
		uint8_t buf[1024*4]; \
		size_t len = sizeof(buf)-1; \
		struct ProcedureStatus psm = {{0,},{0,},{0,}}; \
		int r; \
		\
		r = ttyn1_format_##XTYPE##_transaction(buf, len, NULL, \
			"sample-xid", &psm, \
			TTYN_SYNOPSIS("xact synopsis %s, %s", "formatted", #XTYPE), \
			TTYN_EXTENSION( \
				TTYN_INSERT_SECTION("key", "value") \
			) \
		); \
		test(r > 0); \
		test->strstr(buf, "xact synopsis formatted, " #XTYPE); \
		test->strstr(buf, "data:"); \
		test->strstr(buf, "base64,"); \
		test->strstr(buf, "[" FTYPE); \
	}

transaction_format(open, "->")
transaction_format(update, "--")
transaction_format(close, "<-")
transaction_format(completed, "<>")
transaction_format(failed, "><")

/**
	// Execute the higher level TTYN.1 logging functions with limited checking.
*/
Test(ttyn1_log_frame)
{
	stf_string_t xid = "test-xid";
	stf_metrics_t psm1 = {
		{0, 1, 2, 3},
		{4, 5, 6},
		{7, 8, 9, 10}
	};
	uint8_t *fbuf;
	const char *files = test->fs_tmp();
	int fd, t = 0, r;

	chdir(files);
	fd = open("frames", O_CREAT|O_TRUNC|O_RDWR|O_CLOEXEC);
	test->truth(fd >= 0);

	r = ttyn1_log_declaration(fd, NULL, "xid",
		TTYN_INSERT_SECTION("test-field", "test-data")
	);
	t += r;
	test->equality(t, lseek(fd, 0, SEEK_CUR));

	r = ttyn1_log_open_transaction(fd, NULL, "xid", &psm1,
		TTYN_SYNOPSIS("Open %s", "synopsis-test"),
		TTYN_EXTENSION(
			TTYN_INSERT_SECTION("@failure-image", "test-absurdity"),
			TTYN_INSERT_ILINE_CONSTANT("Absurdity details.")
		)
	);
	t += r;
	test->equality(t, lseek(fd, 0, SEEK_CUR));

	r = ttyn1_log_notice(fd, NULL, "xid",
		TTYN_SYNOPSIS("notification %s", "log-message-test"),
		TTYN_EXTENSION(
			TTYN_INSERT_SECTION("type", "notification-message"),
			TTYN_INSERT_ILINE_CONSTANT("Absurdity details.")
		)
	);
	t += r;
	test->equality(t, lseek(fd, 0, SEEK_CUR));

	r = ttyn1_log_warning(fd, NULL, "xid",
		TTYN_SYNOPSIS("warning %s", "log-message-test"),
		TTYN_EXTENSION(
			TTYN_INSERT_SECTION("type", "warning-message")
		)
	);
	t += r;
	test->equality(t, lseek(fd, 0, SEEK_CUR));

	r = ttyn1_log_error(fd, NULL, "xid",
		TTYN_SYNOPSIS("error %s", "log-message-test"),
		TTYN_EXTENSION(
			TTYN_INSERT_SECTION("type", "error-messsage")
		)
	);
	t += r;
	test->equality(t, lseek(fd, 0, SEEK_CUR));

	r = ttyn1_log_close_transaction(fd, NULL, "xid", &psm1,
		TTYN_SYNOPSIS("Closed %s", "synopsis-test"),
		TTYN_EXTENSION()
	);
	t += r;
	test->equality(t, lseek(fd, 0, SEEK_CUR));

	write(fd, "\0", 1);
	lseek(fd, 0, SEEK_SET);
	fbuf = malloc(t+1);
	test->equality(t+1, read(fd, fbuf, (size_t) t+1));

	{
		const char *prefix = "[!? PROTOCOL: ";
		const char *url_start = "http://";
		const char *url = "http://fault.io/protocol/status/frames tty-notation-1";

		test->memcmp(prefix, fbuf, strlen(prefix));
		test->memcmp(url, test->strstr(fbuf, url_start), strlen(url));
	}

	// No interfaces to fully structure frames, so just check
	test->strstr(fbuf, "Open synopsis-test");
	test->strstr(fbuf, "warning log-message-test");
	test->strstr(fbuf, "error log-message-test");
	test->strstr(fbuf, "Closed synopsis-test");

	unlink("frames");
	free(fbuf);
}
