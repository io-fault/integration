<?xml version="1.0" encoding="utf-8"?>
<?xml-library symbol="factor"?>
<xsl:transform version="1.0"
	xmlns="http://www.w3.org/1999/xhtml"
	xmlns:l="http://fault.io/xml/literal"
	xmlns:exsl="http://exslt.org/common"
	xmlns:set="http://exslt.org/sets"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	xmlns:ctl="http://fault.io/xml/control"
	xmlns:f="http://fault.io/xml/factor"
	xmlns:t="http://fault.io/xml/test"
	xmlns:txt="http://fault.io/xml/text"
	xmlns:idx="http://fault.io/xml/filesystem#index"
	xmlns:ctx="http://fault.io/xml/factor#context"
	xmlns:df="http://fault.io/xml/factor#functions"
	xmlns:func="http://exslt.org/functions"
	xmlns:str="http://exslt.org/strings"
	xmlns:fault="http://fault.io/xml/xpath"
	xmlns:Factor="http://fault.io/xpath#Factor"
	xmlns:py="http://fault.io/xml/python"
	xmlns:xi="http://www.w3.org/2001/XInclude"
	extension-element-prefixes="func exsl"
	exclude-result-prefixes="py l f xsl exsl set str fault ctx df">

	<!--
		# Transform xml/factor source XML into a cross-referenced XHTML document.
	!-->

	<xsl:import href="context.xml"/>
	<xsl:import href="page.xml"/>

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
		df:keep="true"
		fault:keep="true"
		Factor:keep="true"
		py:keep="true"
	/>

	<xsl:param name="python.version" select="'3'"/>
	<xsl:param name="python.docs" select="concat('https://docs.python.org/', $python.version, '/library/')"/>

	<xsl:param name="document_index"/>
	<xsl:param name="reference_suffix" select="''"/>
	<xsl:param name="title_suffix" select="'Documentation'"/>

	<!-- reference to profile measurements -->
	<xsl:param name="metrics_profile" select="''"/>

	<xsl:param name="metrics.profile">
		<xsl:if test="$metrics_profile != ''">
			<xsl:copy-of select="document($metrics_profile)"/>
		</xsl:if>
	</xsl:param>

	<!-- overview of build -->
	<xsl:output
		method="xml" version="1.0" encoding="utf-8"
		omit-xml-declaration="no"
		doctype-system="http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd"
		doctype-public="-//W3C//DTD XHTML 1.0 Strict//EN"
		indent="no"/>

	<xsl:variable name="ctx.index" select="document($document_index)/idx:map/idx:item"/>

	<xsl:variable name="ctx.documentation.fragment">
		<xsl:for-each select="$ctx.index[contains(@key, 'documentation')]/@key">
			<token><xsl:value-of select="string(.)"/></token>
		</xsl:for-each>
	</xsl:variable>

	<xsl:variable name="ctx.documentation" select="exsl:node-set($ctx.documentation.fragment)/*"/>

	<xsl:template match="/">
		<xsl:apply-templates select="/f:factor"/>
		<!--
			<xsl:for-each select="idx:map/idx:item">
				<xsl:variable name="fd" select="document(concat('file://', ./text()))"/>

				<exsl:document href="{@key}"
						method="xml" version="1.0" encoding="utf-8"
						omit-xml-declaration="no"
						doctype-system="http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd"
						doctype-public="-//W3C//DTD XHTML 1.0 Strict//EN"
						indent="no">
				</exsl:document>
			</xsl:for-each>
		!-->
	</xsl:template>
</xsl:transform>
