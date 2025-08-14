/**
	// Validate filesystem tools.
*/
#include <fault/libc.h>

#define TEST_SUITE_EXTENSION
#include <fault/test.h>

Test(fs_tmp_without_content)
{
	const char *tmp = test->fs_tmp();
	struct stat s;

	test->truth(!stat(test->fs_tmp(), &s));
	test->truth(S_ISDIR(s.st_mode));
	test->strcmp(tmp, allocate_fs_tmp());
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
}
