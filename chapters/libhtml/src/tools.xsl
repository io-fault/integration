<?xml version="1.0" encoding="utf-8"?>
<?xml-library symbol="tools"?>
<!--
	# Support module for working with fragments XML.
!-->
<xsl:transform version="1.0"
	xmlns="http://www.w3.org/1999/xhtml"
	xmlns:l="http://fault.io/xml/literal"
	xmlns:exsl="http://exslt.org/common"
	xmlns:set="http://exslt.org/sets"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	xmlns:ctl="http://fault.io/xml/control"
	xmlns:f="http://fault.io/xml/fragments"
	xmlns:t="http://fault.io/xml/test"
	xmlns:txt="http://fault.io/xml/text"
	xmlns:idx="http://fault.io/xml/filesystem#index"
	xmlns:ctx="http://fault.io/xml/factor#context"
	xmlns:func="http://exslt.org/functions"
	xmlns:str="http://exslt.org/strings"
	xmlns:fault="http://fault.io/xml/xpath"
	xmlns:Factor="http://fault.io/xpath#Factor"
	xmlns:xi="http://www.w3.org/2001/XInclude"
	extension-element-prefixes="func exsl"
	exclude-result-prefixes="py l f xsl exsl set str fault ctx">

	<xsl:import href="context.xml"/>

	<ctl:namespaces
		exsl:keep="true"
		func:keep="true"
		set:keep="true"
		str:keep="true"
		f:keep="true"
		l:keep="true"
		t:keep="true"
		txt:keep="true"
		idx:keep="true"
		ctx:keep="true"
		fault:keep="true"
		Factor:keep="true"
	/>

	<xsl:param name="python.version" select="'3'"/>
	<xsl:param name="python.docs"
		select="concat('https://docs.python.org/', $python.version, '/library/')"/>

	<xsl:template name="fragment-qname">
		<xsl:param name="element" select="."/>
		<xsl:value-of select="concat($element/@factor, '.', $element/@name)"/>
	</xsl:template>

	<xsl:template name="fragment-nlines">
		<xsl:param name="src"/>
		<xsl:value-of select="((number($src/@stop)+1) - number($src/@start))"/>
	</xsl:template>

	<xsl:template name="fragment-measure">
		<xsl:param name="src"/>
		<xsl:variable name="n">
			<xsl:call-template name="fragment-nlines">
				<xsl:with-param name="src" select="$src"/>
			</xsl:call-template>
		</xsl:variable>

		<xsl:variable name="total.line.count" select="sum(ctx:factor($src)/f:*/f:source/@stop)"/>
		<xsl:variable name="p" select="($n div $total.line.count) * 100"/>

		<xsl:value-of select="concat($n, ' lines ', format-number($p, '###.##'), '%')"/>
	</xsl:template>

	<xsl:template name="fragment-measure-if">
		<xsl:param name="src"/>

		<xsl:if test="$src/@stop and $src/@start">
			<xsl:call-template name="fragment-measure">
				<xsl:with-param name="src" select="$src"/>
			</xsl:call-template>
		</xsl:if>
	</xsl:template>

	<xsl:template name="fragment-reference">
		<xsl:param name="element" select="."/>

		<xsl:choose>
			<xsl:when test="not($element)">
				<xsl:value-of select="concat($python.docs, 'functions.html#object')"/>
			</xsl:when>

			<xsl:when test="$element/@source = 'builtin'">
				<!-- builtin source, maybe not builtins module -->
				<xsl:choose>
					<!-- special cases for certain builtins -->
					<xsl:when test="$element/@module = 'builtins'">
						<xsl:choose>
							<!--
								# types.ModuleType is identified as existing in builtins, which is a lie
							!-->
							<xsl:when test="$element/@name = 'module'">
								<xsl:value-of select="concat($python.docs, 'types.html#types.ModuleType')"/>
							</xsl:when>

							<!--
								# for whatever reason, the id is "func-str" and not "str"
							!-->
							<xsl:when test="$element/@name = 'str'">
								<xsl:value-of select="concat($python.docs, 'functions.html#func-str')"/>
							</xsl:when>

							<xsl:otherwise>
								<!-- most builtins are documented in functions.html -->
								<xsl:value-of select="concat($python.docs, 'functions.html#', $element/@name)"/>
							</xsl:otherwise>
						</xsl:choose>
					</xsl:when>
					<xsl:otherwise>
						<!-- not a builtins -->
						<xsl:value-of select="concat($python.docs, $element/@factor, '.html')"/>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:when>
			<xsl:when test="$element/@source = 'site-packages'">
				<xsl:value-of select="concat($python.docs, $element/@factor, '.html')"/>
			</xsl:when>
			<xsl:when test="$element/@factor = $element/ancestor::f:factor/f:module/@name">
				<xsl:value-of select="concat('#', $element/@name)"/>
			</xsl:when>
			<xsl:otherwise>
				<!--
					# In corpus.
				!-->
				<xsl:value-of select="concat($element/@factor, '#', $element/@name)"/>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>
</xsl:transform>

