#include "clang-c/Index.h"
#include <stdio.h>
#include <fault/roles.h>

int print_xml_attribute(FILE *, char *, char *); /* attribute identifier and data */
int print_xml_number_attribute(FILE *, char *, unsigned long); /* attribute identifier and data */
int print_xml_string_attribute(FILE *, char *, CXString); /* attribute identifier and data */
int print_xml_identifier(FILE *, char *); /* attribute identifier and data */
int print_xml_text(FILE *, char *);
int print_xml_open(FILE *, char *);
int print_xml_enter(FILE *);
int print_xml_empty(FILE *);
int print_xml_close(FILE *, char *);

static enum CXChildVisitResult visitor(CXCursor cursor, CXCursor parent, CXClientData cd);

static void
print_origin(FILE *fp, CXCursor c)
{
	CXSourceRange range = clang_getCursorExtent(c);	
	CXSourceLocation srcloc = clang_getRangeStart(range);
	CXFile file;
	unsigned int line, offset, column;

	clang_getSpellingLocation(srcloc, &file, &line, &column, &offset);
	print_xml_string_attribute(fp, "origin", clang_getFileName(file));
}

static int
print_source_location(FILE *fp, CXCursor c)
{
	CXSourceRange range = clang_getCursorExtent(c);	
	CXSourceLocation start = clang_getRangeStart(range);
	CXSourceLocation stop = clang_getRangeEnd(range);
	CXFile start_file, stop_file;
	unsigned int start_line, stop_line, start_offset, stop_offset, start_column, stop_column;

	clang_getSpellingLocation(start, &start_file, &start_line, &start_column, &start_offset);
	clang_getSpellingLocation(stop, &stop_file, &stop_line, &stop_column, &stop_offset);

	print_xml_open(fp, "start");
	print_xml_number_attribute(fp, "line", start_line);
	print_xml_number_attribute(fp, "column", start_column);
	print_xml_number_attribute(fp, "offset", start_offset);
	print_xml_empty(fp);

	print_xml_open(fp, "stop");
	print_xml_number_attribute(fp, "line", stop_line);
	print_xml_number_attribute(fp, "column", stop_column);
	print_xml_number_attribute(fp, "offset", stop_offset);
	print_xml_empty(fp);

	return(0);
}

static int
print_spelling_identifier(FILE *fp, CXCursor c)
{
	CXString s = clang_getCursorSpelling(c);
	char *cs = clang_getCString(s);

	print_xml_identifier(fp, cs);
	clang_disposeString(s);
}

static int
print_qualifiers(FILE *fp, CXType t, enum CXTypeKind k)
{
	int r = 0;
	print_xml_open(fp, "qualifiers");

	switch (k)
	{
		case CXType_Enum:
			print_xml_attribute(fp, "type", "enum");
		break;

		case CXType_IncompleteArray:
			print_xml_attribute(fp, "type", "array");
			print_xml_number_attribute(fp, "elements", (unsigned long) clang_getArraySize(t));
		break;

		case CXType_VariableArray:
			print_xml_attribute(fp, "type", "array");
			print_xml_number_attribute(fp, "elements", (unsigned long) clang_getArraySize(t));
		break;

		case CXType_Vector:
			print_xml_attribute(fp, "type", "vector");
		break;

		case CXType_Typedef:
			print_xml_attribute(fp, "type", "typedef");
			r = 1;
		break;

		default:
			if (k >= 100)
				print_xml_attribute(fp, "type", "pointer");
			else
				print_xml_attribute(fp, "type", "data");
		break;
	}

	if (clang_isConstQualifiedType(t))
		print_xml_attribute(fp, "const", "true");

	if (clang_isVolatileQualifiedType(t))
		print_xml_attribute(fp, "volatile", "true");

	if (clang_isRestrictQualifiedType(t))
		print_xml_attribute(fp, "restrict", "true");

	print_xml_empty(fp);
	return(r);
}

static int
print_type(FILE *fp, CXCursor c, CXType ct)
{
	CXCursor dec = clang_getTypeDeclaration(ct);
	CXType xt = ct;
	enum CXTypeKind k = xt.kind;
	unsigned long indirection_level = 0;
	long long i = -1;

	while (k >= 100)
	{
		if (k == CXType_Typedef)
			break;

		xt = clang_getPointeeType(xt);
		k = xt.kind;
		++indirection_level;
	}

	/* Does not handle inline defintions */
	print_xml_open(fp, "type");

	if (!clang_Cursor_isNull(dec) && dec.kind != CXCursor_NoDeclFound)
	{
		print_spelling_identifier(fp, dec);
		print_origin(fp, dec);
	}
	else
	{
		print_xml_string_attribute(fp, "identifier", clang_getTypeSpelling(xt));
	}

	print_xml_string_attribute(fp, "display", clang_getTypeSpelling(ct));
	print_xml_string_attribute(fp, "kind", clang_getTypeKindSpelling(k));

	i = clang_Type_getAlignOf(xt);
	if (i >= 0)
		print_xml_number_attribute(fp, "align", i);

	i = clang_Type_getSizeOf(xt);
	if (i >= 0)
		print_xml_number_attribute(fp, "size", i);

	print_xml_enter(fp);

	{
		xt = ct;
		k = ct.kind;

		if (!print_qualifiers(fp, xt, k))
		{
			while (k >= 100)
			{
				xt = clang_getPointeeType(xt);
				k = xt.kind;
				if (print_qualifiers(fp, xt, k))
					break;
			}
		}
	}

	print_xml_close(fp, "type");
}

static int
print_comment(FILE *fp, CXCursor c)
{
	CXString comment = clang_Cursor_getRawCommentText(c);
	char *comment_str = clang_getCString(comment);

	if (comment_str != NULL)
	{
		print_xml_open(fp, "comment");
		print_xml_attribute(fp, "xml:space", "preserve");
		fprintf(fp, ">");
		print_xml_text(fp, comment_str);
		print_xml_close(fp, "comment");
	}

	clang_disposeString(comment);

	return(0);
}

static enum CXChildVisitResult
callable(CXCursor parent, CXCursor cursor, CXClientData cd,
	enum CXCursorKind kind, enum CXVisibilityKind vis, enum CXAvailabilityKind avail
)
{
	FILE *fp = (FILE *) cd;
	CXCursor arg;
	int i = 0, nargs = clang_Cursor_getNumArguments(cursor);

	print_source_location(fp, cursor);
	print_comment(fp, cursor);

	/*
	 * Don't run visit children as it's only interested in arguments.
	 */
	while (i < nargs)
	{
		CXCursor arg = clang_Cursor_getArgument(cursor, i);
		CXType ct = clang_getCursorType(arg);

		print_xml_open(fp, "parameter");
		print_spelling_identifier(fp, arg);
		fprintf(fp, ">");
		print_type(fp, arg, ct);
		print_xml_close(fp, "parameter");

		++i;
	}

	print_xml_open(fp, "return");
	fprintf(fp, ">");
	print_type(fp, cursor, clang_getResultType(clang_getCursorType(cursor)));
	print_xml_close(fp, "return");

	return(CXChildVisit_Continue);
}

static enum CXChildVisitResult
print_enumeration(CXCursor parent, CXCursor cursor, CXClientData cd,
	enum CXCursorKind kind, enum CXVisibilityKind vis, enum CXAvailabilityKind avail
)
{
	FILE *fp = (FILE *) cd;
	CXType t;

	print_source_location(fp, cursor);
	print_comment(fp, cursor);

	t = clang_getEnumDeclIntegerType(cursor);
	print_type(fp, cursor, t);

	clang_visitChildren(cursor, visitor, cd);

	return(CXChildVisit_Continue);
}

static const char *
node_element_name(enum CXCursorKind kind)
{
	switch (kind)
	{
		case CXCursor_ObjCImplementationDecl:
			return("implementation");

		case CXCursor_ObjCCategoryImplDecl:
			return("category.implementation");

		case CXCursor_ObjCCategoryDecl:
			return("category");

		case CXCursor_ObjCInterfaceDecl:
			return("interface");

		case CXCursor_ObjCProtocolDecl:
			return("protocol");

		case CXCursor_TypedefDecl:
			return("typedef");

		case CXCursor_EnumDecl:
			return("enumeration");

		case CXCursor_EnumConstantDecl:
			return("value");

		case CXCursor_MacroDefinition:
			return("macro");

		case CXCursor_ObjCInstanceMethodDecl:
		case CXCursor_ObjCClassMethodDecl:
		case CXCursor_CXXMethod:
			return("method");

		case CXCursor_FunctionDecl:
			return("function");

		case CXCursor_UnionDecl:
			return("union");

		case CXCursor_StructDecl:
			return("structure");

		case CXCursor_ClassDecl:
			return("class");

		case CXCursor_CXXFinalAttr:
		case CXCursor_CXXOverrideAttr:
		case CXCursor_FieldDecl:
			return("field");

		case CXCursor_NamespaceAlias:
			return("namespace.alias");

		case CXCursor_Namespace:
			return("namespace");

		default:
			return("unknown-type");
	}

	return("switch-passed-with-default");
}

static void
print_contexts(FILE *fp, CXCursor c)
{
	CXCursor parent;
	parent = clang_getCursorSemanticParent(c);

	while (parent.kind != CXCursor_TranslationUnit)
	{
		print_xml_open(fp, "context");
		print_spelling_identifier(fp, parent);
		print_xml_attribute(fp, "element", (char *) node_element_name(parent.kind));
		print_origin(fp, parent);
		print_xml_empty(fp);

		parent = clang_getCursorSemanticParent(parent);
	}
}

static void
print_collection(FILE *fp, CXCursor c, CXClientData cd, const char *element_name)
{
	print_xml_open(fp, element_name);
	print_spelling_identifier(fp, c);
	print_xml_enter(fp);
	print_comment(fp, c);

	print_contexts(fp, c);
	clang_visitChildren(c, visitor, cd);
	print_xml_close(fp, element_name);
}

/**
 * visit the declaration nodes emitting structure and documentation strings.
 */
static enum CXChildVisitResult
visitor(CXCursor cursor, CXCursor parent, CXClientData cd)
{
	static CXString last_file = {0,};
	enum CXChildVisitResult ra = CXChildVisit_Continue;

	enum CXCursorKind kind = clang_getCursorKind(cursor);
	enum CXVisibilityKind vis = clang_getCursorVisibility(cursor);
	enum CXAvailabilityKind avail = clang_getCursorAvailability(cursor);
	FILE *fp = (FILE *) cd;

	CXSourceLocation location = clang_getCursorLocation(cursor);

	if (clang_Location_isFromMainFile(location) == 0)
	{
		CXString filename;
		unsigned int line, column;

		/* Note included files */
		clang_getPresumedLocation(location, &filename, &line, &column);

		if (clang_getCString(last_file) == NULL || strcmp(clang_getCString(last_file), clang_getCString(filename)) != 0)
		{
			print_xml_open(fp, "file");
			print_xml_attribute(fp, "path", clang_getCString(filename));
			print_xml_empty(fp);
			if (clang_getCString(last_file) != NULL)
				clang_disposeString(last_file);
			last_file = filename;
		}

		return(ra);
	}

	switch (kind)
	{
		case CXCursor_TranslationUnit:
			break;

		case CXCursor_TypedefDecl:
		{
			CXType real_type = clang_getTypedefDeclUnderlyingType(cursor);
			print_xml_open(fp, "typedef");
			print_spelling_identifier(fp, cursor);
			print_xml_enter(fp);
			print_type(fp, cursor, real_type);
			print_xml_close(fp, "typedef");
		}
		break;

		case CXCursor_EnumDecl:
		{
			print_xml_open(fp, "enumeration");
			print_spelling_identifier(fp, cursor);
			print_xml_enter(fp);
			ra = print_enumeration(parent, cursor, cd, kind, vis, avail);
			print_xml_close(fp, "enumeration");
		}
		break;

		case CXCursor_EnumConstantDecl:
		{
			print_xml_open(fp, "value");
			print_spelling_identifier(fp, cursor);
			print_xml_enter(fp);
			fprintf(fp, "%lld", clang_getEnumConstantDeclValue(cursor));
			print_xml_close(fp, "value");
		}
		break;

		case CXCursor_MacroExpansion:
			break;
		case CXCursor_PreprocessingDirective:
			break;

		case CXCursor_InclusionDirective:
			break;

		case CXCursor_MacroDefinition:
			if (clang_isCursorDefinition(cursor) == 0)
				return(ra);

			print_xml_open(fp, "macro");
			print_spelling_identifier(fp, cursor);
			print_xml_enter(fp);
			ra = callable(parent, cursor, cd, kind, vis, avail);
			print_xml_close(fp, "macro");
		break;

		case CXCursor_ObjCInstanceMethodDecl:
		case CXCursor_ObjCClassMethodDecl:
		case CXCursor_CXXMethod:
		{
			CXCursor cclass;

			if (clang_isCursorDefinition(cursor) == 0)
				return(ra);

			print_xml_open(fp, "method");
			print_spelling_identifier(fp, cursor);
			print_xml_enter(fp);
			print_contexts(fp, cursor);

			ra = callable(parent, cursor, cd, kind, vis, avail);
			print_xml_close(fp, "method");
		}
		break;

		case CXCursor_FunctionDecl:
			if (clang_isCursorDefinition(cursor) == 0)
				return(ra);

			print_xml_open(fp, "function");
			print_spelling_identifier(fp, cursor);
			print_xml_enter(fp);
			print_contexts(fp, cursor);

			ra = callable(parent, cursor, cd, kind, vis, avail);
			print_xml_close(fp, "function");
		break;

		case CXCursor_UnionDecl:
		{
			if (clang_isCursorDefinition(cursor))
				return(ra);

			print_xml_open(fp, "union");
			print_spelling_identifier(fp, cursor);
			print_xml_enter(fp);
			print_comment(fp, cursor);

			clang_visitChildren(cursor, visitor, cd);

			print_xml_close(fp, "union");
		}
		break;

		case CXCursor_StructDecl:
			print_collection(fp, cursor, cd, "structure");
		break;

		case CXCursor_ObjCImplementationDecl:
			print_collection(fp, cursor, cd, "implementation");
		break;

		case CXCursor_ObjCCategoryImplDecl:
			print_collection(fp, cursor, cd, "category.implementation");
		break;

		case CXCursor_ObjCInterfaceDecl:
			print_collection(fp, cursor, cd, "interface");
		break;

		case CXCursor_ObjCCategoryDecl:
			print_collection(fp, cursor, cd, "category");
		break;

		case CXCursor_ObjCProtocolDecl:
			print_collection(fp, cursor, cd, "protocol");
		break;

		case CXCursor_ClassDecl:
			print_collection(fp, cursor, cd, "class");
		break;

		case CXCursor_ObjCSynthesizeDecl:
			break;
		case CXCursor_ObjCDynamicDecl:
			break;

		case CXCursor_IBActionAttr:
		case CXCursor_IBOutletAttr:
		case CXCursor_IBOutletCollectionAttr:
		case CXCursor_CXXFinalAttr:
		case CXCursor_CXXOverrideAttr:
		case CXCursor_ObjCPropertyDecl:
		case CXCursor_ObjCIvarDecl:
		case CXCursor_FieldDecl:
		{
			print_xml_open(fp, "field");
			print_spelling_identifier(fp, cursor);
			print_xml_enter(fp);
			print_comment(fp, cursor);

			print_type(fp, cursor, clang_getCursorType(cursor));

			print_xml_close(fp, "field");
		}
		break;

		case CXCursor_TypeAliasDecl:
			break;

		case CXCursor_NamespaceAlias:
		{
			print_xml_open(fp, "namespace");
			print_spelling_identifier(fp, cursor);
			print_xml_attribute(fp, "target", "...");
			print_xml_empty(fp);
		}
		break;

		case CXCursor_Namespace:
		{
			print_xml_open(fp, "namespace");
			print_spelling_identifier(fp, cursor);
			print_xml_enter(fp);
			print_comment(fp, cursor);

			print_contexts(fp, cursor);
			print_xml_close(fp, "namespace");

			clang_visitChildren(cursor, visitor, cd);
		}
		break;

		case CXCursor_LinkageSpec:
			break;
		case CXCursor_Constructor:
			break;
		case CXCursor_Destructor:
			break;
		case CXCursor_ConversionFunction:
			break;
		case CXCursor_TemplateTypeParameter:
			break;
		case CXCursor_NonTypeTemplateParameter:
			break;
		case CXCursor_TemplateTemplateParameter:
			break;
		case CXCursor_FunctionTemplate:
			break;
		case CXCursor_ClassTemplate:
			break;
		case CXCursor_ClassTemplatePartialSpecialization:
			break;
		case CXCursor_UsingDirective:
			break;
		case CXCursor_UsingDeclaration:
			break;
		case CXCursor_CXXAccessSpecifier:
			break;

		case CXCursor_ParmDecl:
			break;
		case CXCursor_VarDecl:
			break;

		case CXCursor_ObjCSuperClassRef:
			break;
		case CXCursor_ObjCProtocolRef:
			break;
		case CXCursor_ObjCClassRef:
			break;
		case CXCursor_ObjCMessageExpr:
			break;
		case CXCursor_ObjCStringLiteral:
			break;
		case CXCursor_ObjCEncodeExpr:
			break;
		case CXCursor_ObjCSelectorExpr:
			break;
		case CXCursor_ObjCProtocolExpr:
			break;
		case CXCursor_ObjCBridgedCastExpr:
			break;
		case CXCursor_ObjCAtTryStmt:
			break;
		case CXCursor_ObjCAtCatchStmt:
			break;
		case CXCursor_ObjCAtFinallyStmt:
			break;
		case CXCursor_ObjCAtThrowStmt:
			break;
		case CXCursor_ObjCAtSynchronizedStmt:
			break;
		case CXCursor_ObjCAutoreleasePoolStmt:
			break;
		case CXCursor_ObjCForCollectionStmt:
			break;

		case CXCursor_NamespaceRef:
			break;
		case CXCursor_TypeRef:
			break;
		case CXCursor_DeclRefExpr:
			break;
		case CXCursor_MemberRefExpr:
			break;
		case CXCursor_AnnotateAttr:
			break;
		case CXCursor_CallExpr:
			break;
		case CXCursor_BlockExpr:
			break;
		case CXCursor_IntegerLiteral:
			break;
		case CXCursor_FloatingLiteral:
			break;
		case CXCursor_ImaginaryLiteral:
			break;
		case CXCursor_StringLiteral:
			break;
		case CXCursor_CharacterLiteral:
			break;
		case CXCursor_ParenExpr:
			break;
		case CXCursor_UnaryOperator:
			break;
		case CXCursor_ArraySubscriptExpr:
			break;
		case CXCursor_BinaryOperator:
			break;
		case CXCursor_CompoundAssignOperator:
			break;
		case CXCursor_ConditionalOperator:
			break;
		case CXCursor_CStyleCastExpr:
			break;
		case CXCursor_CompoundLiteralExpr:
			break;
		case CXCursor_InitListExpr:
			break;
		case CXCursor_AddrLabelExpr:
			break;
		case CXCursor_StmtExpr:
			break;
		case CXCursor_GenericSelectionExpr:
			break;
		case CXCursor_GNUNullExpr:
			break;
		case CXCursor_UnaryExpr:
			break;
		case CXCursor_PackExpansionExpr:
			break;
		case CXCursor_SizeOfPackExpr:
			break;
		case CXCursor_LabelStmt:
			break;
		case CXCursor_CompoundStmt:
			break;
		case CXCursor_CaseStmt:
			break;
		case CXCursor_DefaultStmt:
			break;
		case CXCursor_IfStmt:
			break;
		case CXCursor_SwitchStmt:
			break;
		case CXCursor_WhileStmt:
			break;
		case CXCursor_DoStmt:
			break;
		case CXCursor_ForStmt:
			break;
		case CXCursor_GotoStmt:
			break;
		case CXCursor_IndirectGotoStmt:
			break;
		case CXCursor_ContinueStmt:
			break;
		case CXCursor_BreakStmt:
			break;
		case CXCursor_ReturnStmt:
			break;
		case CXCursor_AsmStmt:
			break;
		case CXCursor_SEHTryStmt:
			break;
		case CXCursor_SEHExceptStmt:
			break;
		case CXCursor_SEHFinallyStmt:
			break;
		case CXCursor_NullStmt:
			break;
		case CXCursor_DeclStmt:
			break;

		case CXCursor_CXXStaticCastExpr:
			break;
		case CXCursor_CXXDynamicCastExpr:
			break;
		case CXCursor_CXXReinterpretCastExpr:
			break;
		case CXCursor_CXXConstCastExpr:
			break;
		case CXCursor_CXXFunctionalCastExpr:
			break;
		case CXCursor_CXXTypeidExpr:
			break;
		case CXCursor_CXXBoolLiteralExpr:
			break;
		case CXCursor_CXXNullPtrLiteralExpr:
			break;
		case CXCursor_CXXThisExpr:
			break;
		case CXCursor_CXXThrowExpr:
			break;
		case CXCursor_CXXNewExpr:
			break;
		case CXCursor_CXXDeleteExpr:
			break;
		case CXCursor_CXXCatchStmt:
			break;
		case CXCursor_CXXTryStmt:
			break;
		case CXCursor_CXXForRangeStmt:
			break;

		case CXCursor_UnexposedAttr:
			break;
		case CXCursor_UnexposedExpr:
			break;
		case CXCursor_UnexposedDecl:
			break;
		case CXCursor_UnexposedStmt:
			break;
		case CXCursor_InvalidCode:
			break;

		default:
		break;
	}

	return(ra);
}

int
main(int argc, const char *argv[])
{
	CXIndex idx = clang_createIndex(0, 0);
	CXTranslationUnit u = clang_parseTranslationUnit(idx, 0, argv, argc, 0, 0, CXTranslationUnit_None);
	CXCursor rc;

	rc = clang_getTranslationUnitCursor(u);
	print_xml_open(stdout, "introspection");
	print_xml_attribute(stdout, "collection", "clang");
	print_xml_string_attribute(stdout, "version", clang_getClangVersion());

	print_xml_enter(stdout);
	clang_visitChildren(rc, visitor, (CXClientData) stdout);
	print_xml_close(stdout, "introspection");

	/* Short lived process */
	#if TEST()
		clang_disposeTranslationUnit(TU);
		clang_disposeIndex(Index);
	#endif

	return(0);
}
