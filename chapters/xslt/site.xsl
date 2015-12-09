<?xml version="1.0" encoding="utf-8"?>
<!--
 ! Transform documentation directory into presentable XHTML
 !-->
<xsl:transform version="1.0"
	xmlns="http://www.w3.org/1999/xhtml"
 xmlns:exsl="http://exslt.org/common"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	xmlns:f="https://fault.io/xml/factor"
	xmlns:e="https://fault.io/xml/eclectic"
	xmlns:idx="https://fault.io/xml/documentation#index"
	xmlns:ctx="https://fault.io/xml/factor#context"
	xmlns:func="http://exslt.org/functions"
	xmlns:str="http://exslt.org/strings"
	extension-element-prefixes="func exsl"
	exclude-result-prefixes="f e xsl exsl str ctx">

	<!-- Everythin inside the site transforms should have precedence -->
	<xsl:import href="page.xsl"/>

 <xsl:param name="python.version" select="'3'"/>
 <xsl:param name="python.docs" select="concat('https://docs.python.org/', $python.version, '/library/')"/>

	<!-- overview of build -->
	<xsl:output
			method="xml"
			encoding="utf-8"
			omit-xml-declaration="no"
			indent="no"/>

 <func:function name="ctx:typname">
  <xsl:param name="name"/>

  <func:result>
			<xsl:choose>
				<xsl:when test="starts-with($name, 'builtins.')">
					<xsl:value-of select="substring-after($name, 'builtins.')"/>
				</xsl:when>
				<xsl:otherwise>
					<xsl:value-of select="$name"/>
				</xsl:otherwise>
			</xsl:choose>
  </func:result>
 </func:function>

 <func:function name="ctx:python.hyperlink">
  <xsl:param name="element" select="."/>

  <func:result>
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
        <!-- types.ModuleType is identified as existing in builtins, which is a lie -->
        <xsl:when test="$element/@name = 'module'">
         <xsl:value-of select="concat($python.docs, 'types.html#types.ModuleType')"/>
        </xsl:when>

        <!-- for whatever reason, the id is "func-str" and not "str" -->
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
       <xsl:value-of select="concat($python.docs, $element/@module, '.html')"/>
      </xsl:otherwise>
     </xsl:choose>
    </xsl:when>
    <xsl:when test="$element/@source = 'site-packages'">
     <xsl:value-of select="concat($python.docs, $element/@module, '.html')"/>
    </xsl:when>
    <xsl:when test="$element/@module = $element/ancestor::f:factor/@name">
     <xsl:value-of select="concat('#', $element/@name)"/>
    </xsl:when>
    <xsl:otherwise>
     <!-- Same site (document collection) -->
     <xsl:value-of select="concat($element/@module, '#', $element/@name)"/>
    </xsl:otherwise>
   </xsl:choose>
  </func:result>
 </func:function>

	<func:function name="ctx:join">
		<xsl:param name="tokens"/>
		<xsl:param name="separator"/>
		<xsl:variable name="first" select="$tokens[position()=1]/text()"/>
		<xsl:variable name="remainder" select="exsl:node-set($tokens[position()!=1])"/>

		<func:result>
			<xsl:choose>
				<xsl:when test="$remainder">
					<xsl:value-of select="concat($first, $separator, ctx:join($remainder, $separator))"/>
				</xsl:when>
				<xsl:otherwise>
					<!-- no more tokens, end of recursion -->
					<xsl:value-of select="$first"/>
				</xsl:otherwise>
			</xsl:choose>
		</func:result>
	</func:function>

	<func:function name="ctx:factor">
		<xsl:param name="element"/>
		<func:result select="$element/ancestor::f:factor"/>
	</func:function>

	<func:function name="ctx:pop">
		<xsl:param name="tokens"/>
		<func:result select="$tokens[position()!=last()]"/>
	</func:function>

	<xsl:variable name="index" select="exsl:node-set(/idx:map/idx:item)"/>

	<func:function name="ctx:identifiers">
		<!-- directives can assign additional identifiers, so we work with a set -->
		<xsl:param name="element"/>
		<func:result select="($element/@identifier | $element/e:directive[@name='id'])"/>
	</func:function>

	<func:function name="ctx:id">
		<!-- build the xml:id for the given element -->
		<xsl:param name="element"/>
		<xsl:variable name="parent" select="$element/.."/>

		<xsl:choose>
			<xsl:when test="$element/@xml:id">
				<func:result select="$element/@xml:id"/>
			</xsl:when>

			<xsl:when test="local-name($parent)='factor'">
				<!-- root object -->
				<func:result select="''"/>
			</xsl:when>

			<xsl:when test="$element/@identifier">
				<!-- find the nearest ancestor with an xml:id attr -->
				<!-- and append the element's identifiier or title to it -->
				<!-- prioritize the element's identifier and fallback to :header: for initial
									sections. -->
  		<func:result select="concat(ctx:id($element/ancestor::*[@xml:id or @identifier][1]), '.', $element/@identifier)"/>
			</xsl:when>

			<xsl:when test="$element[local-name()='section' and not(@identifier)]">
				<func:result select="'.header'"/>
			</xsl:when>

			<xsl:otherwise>
				<!--<xsl:variable name="prefix" select="(($element/ancestor::*[@xml:id][1]/@xml:id) | exsl:node-set('factor.'))"/>-->
  		<func:result select="''"/>
			</xsl:otherwise>
		</xsl:choose>
	</func:function>

	<func:function name="ctx:prepare-id">
		<!-- build the xml:id for the given element -->
		<xsl:param name="idstr"/>
		<func:result select="string(str:replace($idstr, ' ', '-'))"/>
	</func:function>

	<func:function name="ctx:contains">
		<!-- check if the given element has the given name for referencing -->
		<xsl:param name="element"/>
		<xsl:param name="name"/>

		<func:result select="$element/*[@identifier=@name]"/>
	</func:function>

	<func:function name="ctx:follow">
		<!-- resolve path points to the final element -->
		<xsl:param name="context"/>
		<xsl:param name="tokens"/>
		<xsl:variable name="name" select="$tokens[position()=1]/text()"/>

		<xsl:choose>
			<xsl:when test="$tokens">
				<func:result select="ctx:follow($context/*[@identifier=$name], tokens[position()>1])"/>
			</xsl:when>
			<xsl:otherwise>
				<func:result select="$context"/>
			</xsl:otherwise>
		</xsl:choose>
	</func:function>

	<func:function name="ctx:scan">
		<!-- scan for the factor path, empty string means there was no factor prefix -->
		<xsl:param name="context"/>
		<xsl:param name="name"/>

		<xsl:variable name="tokens" select="str:tokenize($name, '.')"/>
		<xsl:variable name="lead" select="$tokens[position()=1]"/>

		<!-- nearest addressable ancestor that has the identifier-->
		<xsl:variable name="ancestor" select="$context/ancestor-or-self::*[*[@identifier=$lead]]"/>
		<xsl:variable name="target" select="$ancestor/*[@identifier=$lead]"/>

		<xsl:choose>
			<!-- scan came to an import -->
			<xsl:when test="local-name($target) = 'import'">
				<xsl:variable name="resource" select="exsl:node-set(document($index[@key=$target/@name]))/f:factor/f:module"/>
				<xsl:variable name="selection" select="ctx:follow($resource, $tokens[position()>1])"/>
				<xsl:variable name="prefix" select="$resource/@name"/>
				<xsl:choose>
					<!-- scan came to an import -->
					<xsl:when test="$selection">
						<func:result select="concat($prefix, '#', ctx:id($selection))"/>
					</xsl:when>
					<xsl:otherwise>
						<func:result select="''"/>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:when>
			<xsl:otherwise>
				<xsl:variable name="selection" select="ctx:follow($target, $tokens[position()>1])"/>
				<xsl:variable name="prefix" select="''"/>
				<xsl:choose>
					<!-- scan came to an import -->
					<xsl:when test="$selection">
						<func:result select="concat($prefix, '#', ctx:id($selection))"/>
					</xsl:when>
					<xsl:otherwise>
						<func:result select="''"/>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:otherwise>
		</xsl:choose>
	</func:function>

	<func:function name="ctx:separate">
		<!-- identify the resource portion of a tokenized reference path -->
		<xsl:param name="index"/>
		<xsl:param name="tokens"/>

		<xsl:variable name="path" select="ctx:join($tokens, '.')"/>
		<xsl:variable name="cwp" select="ctx:pop($tokens)"/>

		<xsl:choose>
			<xsl:when test="$index[@key=$path]">
				<func:result select="$path"/>
			</xsl:when>

			<xsl:when test="not($cwp)">
				<!-- not in our factor hierarchy -->
				<func:result select="''"/>
			</xsl:when>

			<xsl:otherwise>
				<func:result select="ctx:separate($index, $cwp)"/>
			</xsl:otherwise>
		</xsl:choose>
	</func:function>

	<func:function name="ctx:split">
		<xsl:param name="path"/>
		<xsl:variable name="factor" select="ctx:separate($index, str:tokenize($path, '.'))"/>
		<func:result select="$factor"/>
	</func:function>

	<func:function name="ctx:site.element">
		<xsl:param name="path"/>
		<xsl:variable name="resource" select="ctx:split($path)"/>
		<xsl:choose>
			<xsl:when test="not($resource)">
				<func:result select="''"/>
			</xsl:when>
			<xsl:otherwise>
				<xsl:variable name="fragment" select="substring-after($path, concat($resource, '.'))"/>
				<xsl:variable name="selection" select="ctx:follow(ctx:document($resource)/f:factor/f:module, str:split($fragment, '.'))"/>
				<func:result select="$selection"/>
			</xsl:otherwise>
		</xsl:choose>
	</func:function>

	<func:function name="ctx:absolute">
		<xsl:param name="path"/>
		<xsl:variable name="factor" select="ctx:separate($index, str:tokenize($path, '.'))"/>
		<xsl:variable name="obj" select="substring(substring-after($path, $factor), 2)"/>
		<xsl:choose>
			<xsl:when test="$obj">
				<func:result select="concat($factor, '#', $obj)"/>
			</xsl:when>
			<xsl:otherwise>
				<!-- just the document -->
				<func:result select="$factor"/>
			</xsl:otherwise>
		</xsl:choose>
	</func:function>

	<func:function name="ctx:qualify">
		<!-- qualify the reference string to make it an absolute path -->
		<xsl:param name="ref"/>

		<func:result>
			<xsl:choose>
				<xsl:when test="starts-with($ref, '.')">
					<xsl:choose>
						<xsl:when test="starts-with($ref, '..')">
							<xsl:choose>
								<xsl:when test="starts-with($ref, '...')">
									<xsl:value-of select="substring($ref, 3)"/>
								</xsl:when>
								<xsl:otherwise>
									<!-- two periods -->
									<xsl:value-of select="concat(/f:factor/f:context/@context, substring($ref, 2))"/>
								</xsl:otherwise>
							</xsl:choose>
						</xsl:when>
						<xsl:otherwise>
							<!-- one period -->
							<xsl:value-of select="concat(/f:factor/f:context/@path, $ref)"/>
						</xsl:otherwise>
					</xsl:choose>
				</xsl:when>
				<xsl:otherwise>
					<xsl:value-of select="''"/>
				</xsl:otherwise>
			</xsl:choose>
		</func:result>
	</func:function>

	<func:function name="ctx:reference">
		<xsl:param name="ref"/>

		<xsl:variable name="quals" select="$ref/@qualifications"/>
		<xsl:variable name="type" select="$ref/@type"/>
		<xsl:variable name="source" select="$ref/@source"/>

		<xsl:variable name="factor" select="$ref/ancestor::f:factor"/>
		<xsl:variable name="context" select="$ref/ancestor::f:*[@xml:id]"/>

		<!-- directory reference -->
		<xsl:variable name="is.directory" select="starts-with($source, '/')"/>

		<xsl:variable name="is.absolute" select="starts-with($source, '...')"/>
		<xsl:variable name="is.context.relative" select="starts-with($source, '..')"/>
		<xsl:variable name="is.project.relative" select="starts-with($source, '.')"/>

		<func:result>
			<xsl:choose>
				<!-- choose the resolution method based on -->
				<xsl:when test="$type = 'hyperlink'">
					<xsl:value-of select="substring($source, 2, string-length($source)-2)"/>
				</xsl:when>

				<xsl:when test="$type = 'section'">
					<!-- nearest f:* element that can be referenced -->
					<xsl:variable name="nearest.re" select="$ref/ancestor::f:*[@xml:id]/@xml:id"/>
					<xsl:value-of select="concat($nearest.re, '.', @source)"/>
				</xsl:when>

				<xsl:when test="$is.directory">
					<!-- TODO -->
					<xsl:value-of select="$source"/>
				</xsl:when>

				<xsl:when test="$factor//*[@xml:id=$source]">
					<xsl:value-of select="concat('#', $source)"/>
				</xsl:when>

				<xsl:otherwise>
					<xsl:variable name="path">
						<!-- resolve the path based on it being absolute or relative -->
						<xsl:choose>
							<xsl:when test="not($is.absolute) and $is.context.relative">
								<xsl:value-of select="concat(ctx:factor($ref)/f:context/@context, substring($source, 2))"/>
							</xsl:when>
							<xsl:when test="not($is.absolute) and $is.project.relative">
								<!-- project relative reference -->
								<xsl:value-of select="concat(ctx:factor($ref)/f:context/@path, $source)"/>
							</xsl:when>
							<xsl:otherwise>
								<xsl:value-of select="substring($source, 3)"/>
							</xsl:otherwise>
						</xsl:choose>
					</xsl:variable>

					<!-- site reference -->
					<xsl:choose>
						<xsl:when test="$is.absolute or $is.context.relative or $is.project.relative">
							<xsl:value-of select="ctx:absolute($path)"/>
						</xsl:when>
						<xsl:otherwise>
							<!-- could be text structure reference -->
							<xsl:variable name="local" select="ctx:scan($ref, $source)"/>
							<xsl:choose>
								<xsl:when test="$local">
									<xsl:value-of select="$local"/>
								</xsl:when>
								<xsl:otherwise>
									<!-- invalid reference -->
									<xsl:value-of select="'#X-INVALID-REFERENCE'"/>
								</xsl:otherwise>
							</xsl:choose>
						</xsl:otherwise>
					</xsl:choose>
				</xsl:otherwise>
			</xsl:choose>
		</func:result>
	</func:function>

	<xsl:variable name="ctx.documentation.fragment">
		<xsl:for-each select="idx:map/idx:item[contains(@key, 'documentation')]/@key">
			<token><xsl:value-of select="string(.)"/></token>
		</xsl:for-each>
	</xsl:variable>

	<xsl:variable name="ctx.documentation" select="exsl:node-set($ctx.documentation.fragment)/*"/>

	<xsl:variable name="ctx.index.fragment">
		<xsl:copy-of select="/"/>
	</xsl:variable>
	<xsl:variable name="ctx.index" select="exsl:node-set($ctx.index.fragment)"/>

	<func:function name="ctx:document">
		<xsl:param name="name"/>
		<func:result select="document(concat('file://', $ctx.index/idx:map/idx:item[@key=$name]/text()))"/>
	</func:function>

	<func:function name="ctx:abstract">
		<xsl:param name="name"/>
		<xsl:variable name="factor" select="ctx:document($name)/f:factor"/>
		<xsl:variable name="fsection" select="$factor/f:*/f:doc/e:section[not(@identifier)][1]"/>
		<xsl:variable name="fpara" select="$fsection/e:paragraph[1]/text()"/>

		<xsl:choose>
			<xsl:when test="$factor/f:context/@path = $name">
				<!-- bottom package module, use project.abstract -->
				<func:result select="string($factor/f:context/@abstract)"/>
			</xsl:when>
			<xsl:otherwise>
				<func:result select="string($fpara)"/>
			</xsl:otherwise>
		</xsl:choose>
	</func:function>

	<func:function name="ctx:icon">
		<!-- scan for the factor path, empty string means there was no factor prefix -->
		<xsl:param name="name"/>

		<xsl:choose>
			<xsl:when test="str:tokenize($name, '.')[last()]/text() = 'documentation'">
				<func:result select="'📚'"/>
			</xsl:when>

			<xsl:when test="$ctx.documentation[text()=$name]">
				<func:result select="'📖'"/>
			</xsl:when>

			<xsl:otherwise>
				<xsl:variable name="doc" select="ctx:document($name)"/>
				<xsl:variable name="project.icon" select="$doc/f:factor/f:context/@icon"/>

				<xsl:choose>
					<xsl:when test="$doc/f:factor/@type = 'namespace'">
						<func:result select="'🏷'"/>
					</xsl:when>
					<xsl:when test="$name = $doc/f:factor/f:context/@path">
						<func:result select="$project.icon"/>
					</xsl:when>
					<xsl:when test="$doc/f:factor/f:subfactor">
						<func:result select="'📦'"/>
					</xsl:when>
					<xsl:otherwise>
						<func:result select="''"/>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:otherwise>
		</xsl:choose>
	</func:function>

	<xsl:template match="/">
		<xsl:for-each select="idx:map/idx:item">
			<xsl:variable name="fd" select="document(concat('file://', ./text()))"/>

			<exsl:document href="{@key}"
					method="xml" version="1.0" encoding="utf-8"
					omit-xml-declaration="no"
					doctype-system="http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd"
					doctype-public="-//W3C//DTD XHTML 1.0 Strict//EN"
					indent="no">
				<xsl:apply-templates select="$fd/f:factor"/>
			</exsl:document>
		</xsl:for-each>
	</xsl:template>

</xsl:transform>
<!--
 ! vim: noet:sw=1:ts=1
 !-->
