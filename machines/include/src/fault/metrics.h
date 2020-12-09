/**
	# Support for directing measurement collections for instrumented processes.
*/
#include <stdlib.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdio.h>
#include <signal.h>
#include <errno.h>
#include <string.h>

#include <sys/types.h>
#include <sys/stat.h>

#ifndef FAULT_MAIN
	#define FAULT_MAIN _fault_application_main
#endif

#ifndef EXECUTABLE_NAME
	#ifdef FACTOR_BASENAME_STR
		#define EXECUTABLE_NAME FACTOR_BASENAME_STR
	#else
		#define EXECUTABLE_NAME "unspecified"
	#endif
#endif

static char _fault_execution_record[4096];

/**
	# Record the execution of the process signaling.
*/
static void
_fault_note_execution_enter(const char *program_name, const char *type)
{
	int fd = -1;
	fd = open(_fault_execution_record, O_WRONLY|O_CREAT);

	if (fd == -1)
	{
		fprintf(stderr,
			"[!* FATAL: `%s` could not be opened for writing]\n", _fault_execution_record);
		fprintf(stderr,
			"\tSystem call 'open' failed(%d): %s.\n", errno, strerror(errno));
		kill(getpid(), SIGUSR2);
		exit(1);
	}

	fchmod(fd, S_IRUSR|S_IWUSR);

	dprintf(fd,
		"name: %s\n"
		"type: %s\n"
		"pid: %d\n"
		"factor: %s\n"
		"",
		program_name,
		type,
		(int) getpid(),
		FACTOR_QNAME_STR
	);

	close(fd);
}

/**
	# Record the exit status of the process and other resource usage information.
	# A measurement snapshot will not have direct access to the status of an exiting
	# process, so the record is noted in this file for subsequent processing.
*/
static void FAULT_MCA
_fault_note_execution_exit(int status)
{
	int fd = -1;
	fd = open(_fault_execution_record, O_WRONLY|O_APPEND);

	dprintf(fd, "status: %d\n", status);

	close(fd);
}

/**
	# Check the (system/envvar)`FAULT_MEASUREMENT_CONTEXT`.
	# Validate that it is empty and can be stat'd.
*/
static void
_fault_validate_context(const char *context_path)
{
	struct stat ctxdir = {0,};
	int r = -1;

	if (context_path == NULL || context_path[0] == '\0')
	{
		fprintf(stderr, "[!* FATAL: FAULT_CAPTURE_DIRECTORY not specified]\n");
		goto fail;
	}

	r = stat(context_path, &ctxdir);
	if (r != 0)
	{
		fprintf(stderr, "[!* FATAL: FAULT_CAPTURE_DIRECTORY is not accessible]\n");
		fprintf(stderr, "\tSystem call 'stat' failed(%d): %s.\n", errno, strerror(errno));
		goto fail;
	}

	return;

	fail:
	{
		kill(getpid(), SIGUSR2);
		exit(1);
	}
}

/**
	# Call the program's real main noting its execution.
*/
int
main(int argc, const char *argv[])
{
	int result;
	char *s;
	int pid = (int) getpid();

	s = getenv("FAULT_CAPTURE_DIRECTORY");
	_fault_validate_context(s);

	snprintf(_fault_execution_record, sizeof(_fault_execution_record)-1, "%s/process-executed.%d", s, pid);

	FAULT_EXECUTABLE_ENTER(EXECUTABLE_NAME, "root");
	result = FAULT_MAIN(argc, argv);
	FAULT_EXECUTABLE_EXIT(result);

	return result;
}
