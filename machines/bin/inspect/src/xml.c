#include <stdio.h>
#include "clang-c/Index.h"

int
print_xml_attribute(FILE *fp, char *attrid, char *str)
{
	fprintf(fp, " %s='%s'", attrid, str);
	return(0);
}

int
print_xml_number_attribute(FILE *fp, char *attrid, unsigned long n)
{
	fprintf(fp, " %s='%lu'", attrid, n);
	return(0);
}

int
print_xml_string_attribute(FILE *fp, char *attrid, CXString cx)
{
	int r;
	char *s;

	s = clang_getCString(cx);
	r = print_xml_attribute(fp, attrid, s);
	clang_disposeString(cx);

	return(r);
}

int
print_xml_identifier(FILE *fp, char *str)
{
	return print_xml_attribute(fp, "identifier", str);
}

/// Print arbitrary raw text in an element's body escaping
/// any field separators as character entities. Numeric
/// form is used to simplify the function.
int
print_xml_text(FILE *fp, char *str)
{
	fprintf(fp, "%s", str);
	return(0);
}

int
print_xml_open(FILE *fp, char *eid)
{
	fprintf(fp, "<%s", eid);
	return(0);
}

int
print_xml_enter(FILE *fp)
{
	fprintf(fp, ">");
	return(0);
}

int
print_xml_empty(FILE *fp)
{
	fprintf(fp, "/>");
	return(0);
}

int
print_xml_close(FILE *fp, char *eid)
{
	fprintf(fp, "</%s>", eid);
	return(0);
}
