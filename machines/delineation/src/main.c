/**
	// Fragments extractor.
*/
#include "clang-c/Index.h"
#include <stdio.h>
#include <fault/libc.h>
#include <fault/fs.h>

struct Image {
	FILE *elements;
	FILE *doce; /* documentation entries */
	FILE *docs;
	FILE *data;
};

static enum CXChildVisitResult visitor(CXCursor cursor, CXCursor parent, CXClientData cd);

static char *
access_string(enum CX_CXXAccessSpecifier aspec)
{
	switch (aspec)
	{
		case CX_CXXPublic:
			return("public");
		break;

		case CX_CXXPrivate:
			return("private");
		break;

		case CX_CXXProtected:
			return("protected");
		break;

		default:
			return(NULL);
		break;
	}

	return(NULL);
}

static void
print_access(FILE *fp, CXCursor cursor)
{
	enum CX_CXXAccessSpecifier access = clang_getCXXAccessSpecifier(cursor);
	print_attribute(fp, "access", access_string(access));
}

static char *
storage_string(enum CX_StorageClass storage)
{
	switch (storage)
	{
		default:
		case CX_SC_Invalid:
		case CX_SC_None:
		case CX_SC_Auto:
			return(NULL);
		break;

		/*
			// Intent of this union is to handle visibility with another attribute;
			// By default, extern will be presumed to be visible unless stated otherwise.
		*/
		case CX_SC_PrivateExtern:
		case CX_SC_Extern:
			return("extern");
		break;

		case CX_SC_Static:
			return("static");
		break;

		case CX_SC_OpenCLWorkGroupLocal:
			return("local");
		break;

		case CX_SC_Register:
			return("register");
		break;
	}

	return(NULL);
}

static void
print_storage(FILE *fp, CXCursor cursor)
{
	enum CX_StorageClass storage = clang_Cursor_getStorageClass(cursor);
	print_attribute(fp, "storage", storage_string(storage));
}

/*
	print_attributes_open(ctx->elements);
	{
		print_attribute(ctx->elements, "element", (char *) node_element_name(parent.kind));
		print_origin(ctx->elements, parent);
	}
	print_attributes_close(ctx->elements);

	print_close(ctx->elements, "context");
*/

static void
print_path(FILE *fp, CXCursor cursor)
{
	CXCursor parent = clang_getCursorSemanticParent(cursor);

	switch (parent.kind)
	{
		case CXCursor_TranslationUnit:
		case CXCursor_FirstInvalid:
			;
		break;

		default:
			print_path(fp, parent);
		break;
	}

	{
		CXString s = clang_getCursorSpelling(cursor);
		const char *cs = clang_getCString(s);

		if (cs != NULL)
		{
			fprintf(fp, quote("%s") ",", cs);
			clang_disposeString(s);
		}
	}
}

static void
print_origin(FILE *fp, CXCursor cursor)
{
	CXSourceRange range = clang_getCursorExtent(cursor);
	CXSourceLocation srcloc = clang_getRangeStart(range);
	CXFile file;
	unsigned int line, offset, column;

	clang_getSpellingLocation(srcloc, &file, &line, &column, &offset);
	print_string_attribute(fp, "origin", clang_getFileName(file));
}

/**
	// Generic means to note the location of the cursor.
*/
static int
print_source_location(FILE *fp, CXSourceRange range)
{
	CXSourceLocation start = clang_getRangeStart(range);
	CXSourceLocation stop = clang_getRangeEnd(range);
	CXFile start_file, stop_file;
	unsigned int start_line, stop_line, start_offset, stop_offset, start_column, stop_column;

	clang_getSpellingLocation(start, &start_file, &start_line, &start_column, &start_offset);
	clang_getSpellingLocation(stop, &stop_file, &stop_line, &stop_column, &stop_offset);

	fputs("[[", fp);
	print_number(fp, "line", start_line);
	print_number(fp, "column", start_column);

	fputs("],[", fp);
	print_number(fp, "line", stop_line);
	print_number(fp, "column", stop_column > 0 ? stop_column-1 : 0);
	fputs("]]", fp);

	return(0);
}

static int
print_spelling_identifier(FILE *fp, CXCursor c)
{
	CXString s = clang_getCursorSpelling(c);
	const char *cs = clang_getCString(s);

	print_identifier(fp, cs);
	clang_disposeString(s);

	return(0);
}

static int
print_type_class(FILE *fp, enum CXTypeKind k)
{
	switch (k)
	{
		case CXType_Enum:
			print_attribute(fp, "meta", "enum");
		break;

		case CXType_IncompleteArray:
			print_attribute(fp, "meta", "array");
		break;

		case CXType_VariableArray:
			print_attribute(fp, "meta", "array");
		break;

		case CXType_Vector:
			print_attribute(fp, "meta", "vector");
		break;

		case CXType_Typedef:
			print_attribute(fp, "meta", "typedef");
		break;

		default:
			if (k >= 100)
				print_attribute(fp, "meta", "pointer");
			else
				print_attribute(fp, "meta", "data");
		break;
	}

	return(0);
}

static int
print_qualifiers(FILE *fp, CXType t)
{
	int c = 0;

	print_enter(fp);
	{
		if (clang_isConstQualifiedType(t))
		{
			print_string(fp, "const", c);
			c += 1;
		}

		if (clang_isVolatileQualifiedType(t))
		{
			print_string(fp, "volatile", c);
			c += 1;
		}

		if (clang_isRestrictQualifiedType(t))
		{
			print_string(fp, "restrict", c);
			c += 1;
		}
	}
	print_exit(fp);
	return(0);
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

	print_enter(fp);
	if (0)
	{
		xt = ct;
		k = ct.kind;

		if (!print_qualifiers(fp, xt))
		{
			while (k >= 100)
			{
				xt = clang_getPointeeType(xt);
				k = xt.kind;
				if (print_qualifiers(fp, xt))
					break;
			}
		}
	}
	print_exit(fp);

	print_attributes_open(fp);
	if (!clang_Cursor_isNull(dec) && dec.kind != CXCursor_NoDeclFound)
	{
		print_spelling_identifier(fp, dec);
		print_origin(fp, dec);
	}
	else
	{
		print_string_attribute(fp, "identifier", clang_getTypeSpelling(xt));
	}

	print_string_attribute(fp, "syntax", clang_getTypeSpelling(ct));
	print_string_attribute(fp, "kind", clang_getTypeKindSpelling(k));

	i = clang_Type_getAlignOf(xt);
	if (i >= 0)
		print_number_attribute(fp, "align", i);

	i = clang_Type_getSizeOf(xt);
	if (i >= 0)
		print_number_attribute(fp, "size", i);

	i = clang_getArraySize(xt);
	if (i >= 0)
	{
		CXType at = xt;
		print_string(fp, "elements", 0);
		print_enter(fp);

		do {
			print_number(fp, NULL, i);
			at = clang_getArrayElementType(at);
			i = clang_getArraySize(at);
		} while (at.kind != CXType_Invalid && i >= 0);

		print_exit(fp);
	}

	print_attributes_close(fp);
	return(0);
}

static bool
print_comment(struct Image *ctx, CXCursor cursor)
{
	CXString comment = clang_Cursor_getRawCommentText(cursor);
	char *comment_str = clang_getCString(comment);

	if (comment_str != NULL)
	{
		fputs("[", ctx->doce);
		print_path(ctx->doce, cursor);
		fputs("],", ctx->doce);

		fputs("[\x22", ctx->docs);
		print_text(ctx->docs, comment_str, true);
		fputs("\x22],", ctx->docs);

		clang_disposeString(comment);
	}
	else
		return(false);

	return(true);
}

static int
print_documented(FILE *fp, CXCursor cursor)
{
	CXSourceRange docarea = clang_Cursor_getCommentRange(cursor);

	if (!clang_Range_isNull(docarea))
	{
		fputs("," quote("documented") ":", fp);
		print_source_location(fp, docarea);
	}

	return(0);
}

/**
	// Describe the callable's type and parameters.
*/
static enum CXChildVisitResult
callable(
	CXCursor parent, CXCursor cursor, CXClientData cd,
	enum CXCursorKind kind,
	enum CXVisibilityKind vis,
	enum CXAvailabilityKind avail)
{
	struct Image *ctx = (struct Image *) cd;
	CXCursor arg;
	int i, nargs = clang_Cursor_getNumArguments(cursor);

	print_open(ctx->elements, "type");
	print_type(ctx->elements, cursor, clang_getResultType(clang_getCursorType(cursor)));
	print_close(ctx->elements, "type");

	for (i = 0; i < nargs; ++i)
	{
		CXCursor arg = clang_Cursor_getArgument(cursor, i);
		CXType ct = clang_getCursorType(arg);

		print_open(ctx->elements, "parameter");
		print_enter(ctx->elements);
		{
			print_open(ctx->elements, "type");
			print_type(ctx->elements, arg, ct);
			print_close(ctx->elements, "type");
		}
		print_exit(ctx->elements);

		print_attributes_open(ctx->elements);
		{
			print_spelling_identifier(ctx->elements, arg);
		}
		print_attributes_close(ctx->elements);

		print_close(ctx->elements, "parameter");
	}

	return(CXChildVisit_Continue);
}

static enum CXChildVisitResult
macro(
	CXCursor parent, CXCursor cursor, CXClientData cd,
	enum CXCursorKind kind,
	enum CXVisibilityKind vis,
	enum CXAvailabilityKind avail)
{
	struct Image *ctx = (struct Image *) cd;
	CXCursor arg;
	int i = 0, nargs = clang_Cursor_getNumArguments(cursor);

	print_comment(ctx, cursor);

	print_enter(ctx->elements);
	{
		if (clang_Cursor_isMacroFunctionLike(cursor))
		{
			while (i < nargs)
			{
				CXCursor arg = clang_Cursor_getArgument(cursor, i);

				print_open_empty(ctx->elements, "parameter");
				print_attributes_open(ctx->elements);
				{
					print_spelling_identifier(ctx->elements, arg);
				}
				print_attributes_close(ctx->elements);
				print_close(ctx->elements, "parameter");

				++i;
			}
		}
	}
	print_exit(ctx->elements);

	print_attributes_open(ctx->elements);
	{
		print_spelling_identifier(ctx->elements, cursor);
		fputs(quote("area") ":", ctx->elements);
		print_source_location(ctx->elements, clang_getCursorExtent(cursor));
		print_documented(ctx->elements, cursor);
	}
	print_attributes_close(ctx->elements);

	return(CXChildVisit_Continue);
}

static enum CXChildVisitResult
print_enumeration(
	CXCursor parent, CXCursor cursor, CXClientData cd,
	enum CXCursorKind kind,
	enum CXVisibilityKind vis,
	enum CXAvailabilityKind avail)
{
	struct Image *ctx = (struct Image *) cd;
	CXType t;

	print_comment(ctx, cursor);

	t = clang_getEnumDeclIntegerType(cursor);
	print_enter(ctx->elements);
	{
		clang_visitChildren(cursor, visitor, cd);
	}
	print_exit(ctx->elements);

	print_attributes_open(ctx->elements);
	{
		print_spelling_identifier(ctx->elements, cursor);
		fputs(quote("area") ":", ctx->elements);
		print_source_location(ctx->elements, clang_getCursorExtent(cursor));
		print_documented(ctx->elements, cursor);
	}
	print_attributes_close(ctx->elements);

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
			return("category-implementation");

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
			return("constant");

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
			return("namespace-alias");

		case CXCursor_Namespace:
			return("namespace");

		default:
			return("unknown");
	}

	return("switch-passed-with-default");
}

static void
print_collection(struct Image *ctx, CXCursor cursor, CXClientData cd, const char *element_name)
{
	print_comment(ctx, cursor);

	print_open(ctx->elements, element_name);

	print_enter(ctx->elements);
	{
		clang_visitChildren(cursor, visitor, cd);
	}
	print_exit(ctx->elements);

	print_attributes_open(ctx->elements);
	{
		print_spelling_identifier(ctx->elements, cursor);
		fputs(quote("area") ":", ctx->elements);
		print_source_location(ctx->elements, clang_getCursorExtent(cursor));
		print_documented(ctx->elements, cursor);
	}
	print_attributes_close(ctx->elements);

	print_close(ctx->elements, element_name);
}

/**
	// Visit the declaration nodes emitting structure and documentation strings.
*/
static enum CXChildVisitResult
visitor(CXCursor cursor, CXCursor parent, CXClientData cd)
{
	struct Image *ctx = (struct Image *) cd;
	static CXString last_file = {0,};
	enum CXChildVisitResult ra = CXChildVisit_Continue;

	enum CXCursorKind kind = clang_getCursorKind(cursor);
	enum CXVisibilityKind vis = clang_getCursorVisibility(cursor);
	enum CXAvailabilityKind avail = clang_getCursorAvailability(cursor);

	CXSourceLocation location = clang_getCursorLocation(cursor);

	if (clang_Location_isFromMainFile(location) == 0)
	{
		CXString filename;
		unsigned int line, column;

		/* Note included files */
		clang_getPresumedLocation(location, &filename, &line, &column);

		if (clang_getCString(last_file) == NULL ||
			strcmp(clang_getCString(last_file), clang_getCString(filename)) != 0)
		{
			if (clang_getCString(filename)[0] != '<')
			{
				print_open_empty(ctx->elements, "include");
				{
					print_attributes_open(ctx->elements);
					{
						print_attribute(ctx->elements, "path", clang_getCString(filename));
					}
					print_attributes_close(ctx->elements);
				}
				print_close(ctx->elements, "include");

				if (clang_getCString(last_file) != NULL)
					clang_disposeString(last_file);

				last_file = filename;
			}
		}

		return(ra);
	}

	switch (kind)
	{
		case CXCursor_TranslationUnit:
			/*
				// Root node already being visited.
			*/
		break;

		case CXCursor_TypedefDecl:
		{
			CXType real_type = clang_getTypedefDeclUnderlyingType(cursor);

			print_comment(ctx, cursor);
			print_open(ctx->elements, "typedef");

			print_enter(ctx->elements);
			{
				print_type(ctx->elements, cursor, real_type);
			}
			print_exit(ctx->elements);

			print_attributes_open(ctx->elements);
			{
				print_spelling_identifier(ctx->elements, cursor);
				fputs(quote("area") ":", ctx->elements);
				print_source_location(ctx->elements, clang_getCursorExtent(cursor));
				print_documented(ctx->elements, cursor);
			}
			print_attributes_close(ctx->elements);

			print_close(ctx->elements, "typedef");
		}
		break;

		case CXCursor_EnumDecl:
		{
			print_open(ctx->elements, "enumeration");
			ra = print_enumeration(parent, cursor, cd, kind, vis, avail);
			print_close(ctx->elements, "enumeration");
		}
		break;

		case CXCursor_EnumConstantDecl:
		{
			print_open_empty(ctx->elements, "constant");

			print_attributes_open(ctx->elements);
			{
				print_spelling_identifier(ctx->elements, cursor);
				print_number_attribute(ctx->elements, "integer", clang_getEnumConstantDeclValue(cursor));
			}
			print_attributes_close(ctx->elements);

			print_close(ctx->elements, "constant");
		}
		break;

		case CXCursor_MacroExpansion:
			/*
				// Link expansion to definition.
			*/
			clang_visitChildren(cursor, visitor, cd);
		break;

		case CXCursor_PreprocessingDirective:
		{
			clang_visitChildren(cursor, visitor, cd);
		}
		break;

		case CXCursor_InclusionDirective:
			break;

		case CXCursor_MacroDefinition:
		{
			const char *m_subtype = "macro";

			if (!clang_Cursor_isMacroFunctionLike(cursor))
				m_subtype = "define";

			print_open(ctx->elements, m_subtype);
			ra = macro(parent, cursor, cd, kind, vis, avail);
			print_close(ctx->elements, m_subtype);
		}
		break;

		case CXCursor_ObjCInstanceMethodDecl:
		case CXCursor_ObjCClassMethodDecl:
		case CXCursor_CXXMethod:
		{
			CXCursor cclass;

			if (clang_isCursorDefinition(cursor) == 0)
				return(ra);

			print_comment(ctx, cursor);
			print_open(ctx->elements, "method");

			print_enter(ctx->elements);
			{
				ra = callable(parent, cursor, cd, kind, vis, avail);
			}
			print_exit(ctx->elements);

			print_attributes_open(ctx->elements);
			{
				print_spelling_identifier(ctx->elements, cursor);
				fputs(quote("area") ":", ctx->elements);
				print_source_location(ctx->elements, clang_getCursorExtent(cursor));
				print_documented(ctx->elements, cursor);
			}
			print_attributes_close(ctx->elements);

			print_close(ctx->elements, "method");
		}
		break;

		case CXCursor_FunctionDecl:
		{
			if (clang_isCursorDefinition(cursor) == 0)
				return(ra);

			print_comment(ctx, cursor);
			print_open(ctx->elements, "function");

			print_enter(ctx->elements);
			{
				ra = callable(parent, cursor, cd, kind, vis, avail);
			}
			print_exit(ctx->elements);

			print_attributes_open(ctx->elements);
			{
				print_spelling_identifier(ctx->elements, cursor);
				fputs(quote("area") ":", ctx->elements);
				print_source_location(ctx->elements, clang_getCursorExtent(cursor));
				print_documented(ctx->elements, cursor);
			}
			print_attributes_close(ctx->elements);

			print_close(ctx->elements, "function");
		}
		break;

		case CXCursor_UnionDecl:
		{
			if (clang_isCursorDefinition(cursor))
				return(ra);

			print_comment(ctx, cursor);

			print_open(ctx->elements, "union");
			print_enter(ctx->elements);
			{
				clang_visitChildren(cursor, visitor, cd);
			}
			print_exit(ctx->elements);

			print_attributes_open(ctx->elements);
			{
				print_spelling_identifier(ctx->elements, cursor);
			}
			print_attributes_close(ctx->elements);

			print_close(ctx->elements, "union");
		}
		break;

		case CXCursor_StructDecl:
			print_collection(ctx, cursor, cd, "structure");
		break;

		case CXCursor_ObjCImplementationDecl:
			print_collection(ctx, cursor, cd, "implementation");
		break;

		case CXCursor_ObjCCategoryImplDecl:
			print_collection(ctx, cursor, cd, "category.implementation");
		break;

		case CXCursor_ObjCInterfaceDecl:
			print_collection(ctx, cursor, cd, "interface");
		break;

		case CXCursor_ObjCCategoryDecl:
			print_collection(ctx, cursor, cd, "category");
		break;

		case CXCursor_ObjCProtocolDecl:
			print_collection(ctx, cursor, cd, "protocol");
		break;

		case CXCursor_ClassDecl:
			print_collection(ctx, cursor, cd, "class");
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
			print_comment(ctx, cursor);

			print_open(ctx->elements, "field");

			print_enter(ctx->elements);
			{
				print_open(ctx->elements, "type");
				print_type(ctx->elements, cursor, clang_getCursorType(cursor));
				print_close(ctx->elements, "type");
			}
			print_exit(ctx->elements);

			print_attributes_open(ctx->elements);
			{
				print_spelling_identifier(ctx->elements, cursor);
			}
			print_attributes_close(ctx->elements);

			print_close(ctx->elements, "field");
		}
		break;

		case CXCursor_TypeAliasDecl:
			break;

		case CXCursor_NamespaceAlias:
		{
			print_open(ctx->elements, "namespace");

			print_attributes_open(ctx->elements);
			{
				print_spelling_identifier(ctx->elements, cursor);
				print_attribute(ctx->elements, "target", "...");
			}
			print_attributes_close(ctx->elements);

			print_close(ctx->elements, "namespace");
		}
		break;

		case CXCursor_Namespace:
		{
			print_comment(ctx, cursor);
			print_open(ctx->elements, "namespace");

			print_enter(ctx->elements);
			{
				clang_visitChildren(cursor, visitor, cd);
			}
			print_exit(ctx->elements);

			print_attributes_open(ctx->elements);
			{
				print_spelling_identifier(ctx->elements, cursor);
			}
			print_attributes_close(ctx->elements);

			print_close(ctx->elements, "namespace");
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
	struct Image ctx;
	CXIndex idx = clang_createIndex(0, 1);
	CXCursor rc;
	CXTranslationUnit u;
	enum CXErrorCode err;
	const char *output, *source;

	/*
		// clang_parseTranslationUnit does not appear to agree that the
		// executable should end in (filename)`.i` so adjust the command name.
		// It would appear that the option parser is (was) sensitive to dot-suffixes.
	*/
	argv[0] = "delineate";
	source = argv[argc-1];

	err = clang_parseTranslationUnit2(idx, NULL, argv, argc, NULL, 0,
		CXTranslationUnit_DetailedPreprocessingRecord, &u);
	if (err != 0)
		return(1);

	rc = clang_getTranslationUnitCursor(u);

	/*
		// Parsed options accessors are not available in libclang?
	*/
	output = argv[argc-2];
	if (fs_mkdir(output) != 0)
	{
		perror("could not create target directory");
		return(1);
	}

	chdir(output);

	ctx.elements = fopen("elements.json", "w");
	ctx.doce = fopen("documented.json", "w");
	ctx.docs = fopen("documentation.json", "w");
	ctx.data = fopen("data.json", "w");

	print_open(ctx.elements, "unit"); /* Translation Unit */
	print_enter(ctx.data);
	print_enter(ctx.docs);
	print_enter(ctx.doce);

	print_enter(ctx.elements);
	{
		clang_visitChildren(rc, visitor, (CXClientData) &ctx);
	}
	print_exit(ctx.elements);

	print_attributes_open(ctx.elements);
	{
		print_string_attribute(ctx.elements, "version", clang_getClangVersion());
		print_attribute(ctx.elements, "engine", "libclang");

		switch (clang_getCursorLanguage(rc))
		{
			case CXLanguage_C:
				print_attribute(ctx.elements, "language", "c");
			break;

			case CXLanguage_ObjC:
				print_attribute(ctx.elements, "language", "objective-c");
			break;

			case CXLanguage_CPlusPlus:
				print_attribute(ctx.elements, "language", "c++");
			break;

			case CXLanguage_Invalid:
			default:
			break;
		}
	}
	print_attributes_close(ctx.elements);

	print_exit_final(ctx.doce);
	print_exit_final(ctx.docs);
	print_exit_final(ctx.data);
	print_close_final(ctx.elements, "unit");

	fclose(ctx.elements);
	fclose(ctx.docs);
	fclose(ctx.doce);
	fclose(ctx.data);

	clang_disposeTranslationUnit(u);
	clang_disposeIndex(idx);

	return(0);
}
