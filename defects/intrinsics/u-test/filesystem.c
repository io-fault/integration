/**
	// Validate filesystem tools.
*/
#include <fault/libc.h>

#define TEST_SUITE_EXTENSION
#define _TEST_HARNESS_FUNCTIONS
#include <fault/test.h>

Test(fs_tmp_without_content)
{
	const char *tmp = test->fs_tmp();
	struct stat s;

	test->truth(!stat(test->fs_tmp(), &s));
	test->truth(S_ISDIR(s.st_mode));
	test->strcmp(tmp, allocate_fs_tmp());

	h_cleanup_tmpdir(test, true);
	test->truth(stat(tmp, &s));
	test->equality(ENOENT, errno);
}

Test(fs_tmp_with_content)
{
	const char *tmp = test->fs_tmp();
	const char fc[] = "#include <stdio.h>\n";
	struct stat s;
	int fd;

	chdir(tmp);
	fd = open("test.c", O_CREAT|O_WRONLY);
	write(fd, fc, sizeof(fc)-1);
	close(fd);

	test->truth(!stat("test.c", &s));
	test->truth(S_ISREG(s.st_mode));
	test->strcmp(tmp, allocate_fs_tmp());

	h_cleanup_tmpdir(test, true);
	test->truth(stat(tmp, &s));
	test->equality(ENOENT, errno);
}

Test(fs_tmpdir_restriction)
{
	const char *current_tmpdir_root = _h_tmpdir_root;
	const char *tde = getenv("TMPDIR");

	unsetenv("TMPDIR");
	test->truth(!h_configure_tmpdir(test->stf_receiver, test->identity->ti_name, "./"));
	test(!)->equality(_h_tmpdir_restriction, NULL);

	// Put things back for single process sequential.
	setenv("TMPDIR", tde, 1);
	_h_tmpdir_restriction = NULL;
	_h_tmpdir_root = current_tmpdir_root;
}

Test(fs_tmp_hash_check)
{
	const char *tmp = test->fs_tmp();
	struct stat s;

	++test->tmpdir_path_hash;
	h_cleanup_tmpdir(test, true);

	test->truth(!stat(test->fs_tmp(), &s));
	test->truth(S_ISDIR(s.st_mode));

	--test->tmpdir_path_hash;
}

Test(fs_tmp_out_of_root)
{
	const char *tmproot = _h_tmpdir_root;
	const char *tmp = test->fs_tmp();
	struct stat s;

	_h_tmpdir_root = "/dev/null";
	h_cleanup_tmpdir(test, true);

	test->truth(!stat(test->fs_tmp(), &s));
	test->truth(S_ISDIR(s.st_mode));

	_h_tmpdir_root = tmproot;
}
