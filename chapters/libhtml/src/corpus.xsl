<?xml version="1.0" encoding="utf-8"?>
<?xml-library symbol="corpus"?>
<!--
	# Construct the corpus index for a set of projects and contexts.
!-->
<xsl:transform version="1.0"
	xmlns="http://www.w3.org/1999/xhtml"
	xmlns:f="http://fault.io/xml/fragments"
	xmlns:l="http://fault.io/xml/literal"
	xmlns:exsl="http://exslt.org/common"
	xmlns:set="http://exslt.org/sets"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	xmlns:ctl="http://fault.io/xml/control"
	xmlns:t="http://fault.io/xml/test"
	xmlns:txt="http://if.fault.io/xml/text"
	xmlns:idx="http://fault.io/xml/filesystem#index"
	xmlns:ctx="http://fault.io/xml/factor#context"
	xmlns:func="http://exslt.org/functions"
	xmlns:str="http://exslt.org/strings"
	xmlns:fault="http://fault.io/xml/xpath"
	xmlns:Factor="http://fault.io/xpath#Factor"
	xmlns:xi="http://www.w3.org/2001/XInclude"
	extension-element-prefixes="func exsl"
	exclude-result-prefixes="py l f xsl exsl set str fault ctx">

	<xsl:import href="factor.xml"/>
	<xsl:param name="title_suffix" select="'Corpus'"/>

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

	<xsl:template select="/">
		<xsl:apply-templates select="/f:factor"/>
	</xsl:template>
</xsl:transform>
