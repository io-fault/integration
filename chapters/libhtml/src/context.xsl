<?xml version="1.0" encoding="utf-8"?>
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

	<!--
		# HTML context support functions and templates.
	!-->

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

	<func:function name="ctx:python.builtin">
		<xsl:param name="string"/>

		<func:result>
			<xsl:choose>
				<!-- types.ModuleType is identified as existing in builtins, which is a lie -->
				<xsl:when test="Factor:exception($string)">
					<xsl:value-of select="concat($python.docs, 'exceptions.html#', $string)"/>
				</xsl:when>

				<xsl:when test="$string = 'None' or $string = 'True' or $string = 'False' or $string = 'Ellipsis' or $string = 'NotImplemented'">
					<xsl:value-of select="concat($python.docs, 'constants.html#', $string)"/>
				</xsl:when>

				<xsl:when test="$string = 'module'">
					<xsl:value-of select="concat($python.docs, 'types.html#types.ModuleType')"/>
				</xsl:when>

				<!-- for whatever reason, the id is "func-str" and not "str" -->
				<xsl:when test="$string = 'str'">
					<xsl:value-of select="concat($python.docs, 'functions.html#func-str')"/>
				</xsl:when>

				<xsl:otherwise>
					<!-- most builtins are documented in functions.html -->
					<xsl:value-of select="concat($python.docs, 'functions.html#', $string)"/>
				</xsl:otherwise>
			</xsl:choose>
		</func:result>
	</func:function>

	<func:function name="ctx:factor">
		<xsl:param name="element"/>
		<func:result select="$element/ancestor::f:factor"/>
	</func:function>

	<func:function name="ctx:identifiers">
		<!-- directives can assign additional identifiers, so we work with a set -->
		<xsl:param name="element"/>
		<func:result select="($element/@identifier | $element/txt:directive[@name='id'])"/>
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

			<xsl:when test="local-name($element)='parameter'">
				<func:result select="concat($parent/@xml:id, '.Parameters.', $element/@identifier)"/>
			</xsl:when>

			<xsl:when test="$element/@identifier">
				<!--
					# Find the nearest ancestor with an xml:id attr
					# and append the element's identifiier or title to it
					# prioritize the element's identifier and fallback to
					# :header: for initial sections.
				!-->
				<func:result select="concat(ctx:id($element/ancestor::*[@xml:id or @identifier][1]), '.', $element/@identifier)"/>
			</xsl:when>

			<xsl:when test="$element[local-name()='section' and not(@identifier)]">
				<xsl:variable name="expr" select="ancestor::f:*[@xml:id]"/>
				<xsl:variable name="prefix">
					<xsl:choose>
						<xsl:when test="$expr">
							<xsl:value-of select="ctx:id($expr)"/>
						</xsl:when>
						<xsl:otherwise>
							<xsl:value-of select="'factor.'"/>
						</xsl:otherwise>
					</xsl:choose>
				</xsl:variable>
				<func:result select="concat($prefix, '.', 'context..section')"/>
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
		<!--
			# Resolve path points to the final element.
		!-->

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
		<!--
			# Scan for the factor path, empty string means there was no factor prefix.
		!-->
		<xsl:param name="context"/>
		<xsl:param name="name"/>

		<xsl:variable name="tokens" select="str:tokenize($name, '.')"/>
		<xsl:variable name="lead" select="$tokens[position()=1]"/>

		<!--
			# Nearest addressable ancestor that has the identifier
		!-->
		<xsl:variable name="ancestor"
			select="
				(
						$context/ancestor-or-self::*/txt:section/txt:dictionary[*[@identifier=$lead]]
					|$context/ancestor-or-self::*[*[@identifier=$lead]]
				)[position()=1]
			"/>

		<xsl:variable name="target" select="$ancestor/*[@identifier=$lead]"/>

		<xsl:message>
			<xsl:value-of select="local-name($target)"/>:
			<xsl:value-of select="$target/@identifier"/>
		</xsl:message>

		<xsl:choose>
			<xsl:when test="local-name($target) = 'import'">
				<!--
					# Scan found an import
				!-->

				<xsl:variable name="resource" select="exsl:node-set(document($ctx.index[@key=$target/@name]))/f:factor/f:module"/>
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

			<xsl:when test="local-name($target) = 'parameter'">
				<func:result select="concat('#', ctx:id($target))"/>
			</xsl:when>

			<xsl:otherwise>
				<xsl:variable name="selection" select="ctx:follow($target, $tokens[position()>1])"/>
				<xsl:variable name="prefix" select="''"/>
				<xsl:choose>
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

		<xsl:variable name="path" select="fault:join('.', $tokens)"/>
		<xsl:variable name="cwp" select="fault:head($tokens)"/>
		<xsl:variable name="item" select="$index[@key=$path]"/>

		<xsl:choose>
			<xsl:when test="$item">
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
		<xsl:variable name="factor" select="ctx:separate($ctx.index, str:tokenize($path, '.'))"/>
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
		<xsl:param name="this" select="''"/>

		<xsl:variable name="tokens" select="fault:split('.', $path)"/>
		<xsl:variable name="factor" select="ctx:separate($ctx.index, $tokens)"/>
		<xsl:variable name="obj" select="substring(substring-after($path, $factor), 2)"/>

		<xsl:choose>
			<xsl:when test="$factor = ''">
				<!-- No factor? No reference -->
				<func:result select="''"/>
			</xsl:when>
			<xsl:when test="$factor != '' and $obj != ''">
				<func:result select="concat($factor, $reference_suffix, '#', $obj)"/>
			</xsl:when>
			<xsl:otherwise>
				<!-- just the document -->
				<func:result select="concat($factor, $reference_suffix)"/>
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

	<func:function name="ctx:element.from.source">
		<xsl:param name="factor"/>
		<xsl:param name="lineno"/>
		<xsl:variable name="d" select="ctx:document($factor)"/>
		<xsl:variable name="s" select="$d//f:source[@start=$lineno]"/>

		<func:result select="$s/.."/>
	</func:function>

	<func:function name="ctx:duration">
		<xsl:param name="string"/>
		<func:result>
			<span class="typed.data">
				<span class="time.duration"><xsl:value-of select="$string"/></span>
			</span>
		</func:result>
	</func:function>

	<!--process reference elements generated by text-->
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
				<!--
					# Choose the initial resolution method based on the type.
				!-->
				<xsl:when test="$type = 'hyperlink'">
					<xsl:value-of select="substring($source, 2, string-length($source)-2)"/>
				</xsl:when>

				<xsl:when test="$type = 'section'">
					<!--
						# Nearest f:* element that can be referenced.
					!-->
					<xsl:variable name="nearest.re" select="$ref/ancestor::f:*[@xml:id]/@xml:id"/>
					<xsl:value-of select="concat($nearest.re, '.', @source)"/>
				</xsl:when>

				<xsl:when test="$is.directory">
					<!--
						# TODO: &/unix/man/2/accept
					!-->
					<xsl:value-of select="$source"/>
				</xsl:when>

				<xsl:when test="$factor//*[@xml:id=$source]">
					<!--
						# Reference is a simple xml:id target local to the document.
					!-->
					<xsl:value-of select="concat('#', $source)"/>
				</xsl:when>

				<xsl:otherwise>
					<!--
						# Resolve dot-separated path entries in order to identify the target.
					!-->
					<xsl:variable name="path">
						<!--
							# Trim leading periods from reference.
						!-->
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
					<xsl:variable name="strsrc" select="string($source)"/>

					<xsl:choose>
						<!--
							# Context Dependent Reference
						!-->
						<xsl:when test="$is.absolute or $is.context.relative or $is.project.relative">
							<xsl:value-of select="/f:factor/@depth"/>
							<xsl:value-of select="ctx:absolute(string($path))"/>
						</xsl:when>
						<xsl:otherwise>
							<!--
								# Could be text structure reference
							!-->
							<xsl:variable name="local" select="ctx:scan($ref, $strsrc)"/>

							<xsl:choose>
								<xsl:when test="starts-with($local, '#')">
									<xsl:value-of select="$local"/>
								</xsl:when>
								<xsl:when test="$local">
									<xsl:value-of select="/f:factor/@depth"/>
									<xsl:value-of select="$local"/>
								</xsl:when>
								<xsl:otherwise>
									<!-- Absolute Path or invalid reference -->
									<xsl:choose>
									 <xsl:when test="contains($strsrc, '.')">
											<xsl:variable name="pair" select="Factor:reference($strsrc)"/>
											<xsl:value-of select="/f:factor/@depth"/>
											<xsl:value-of select="concat($python.docs, $pair[1], $reference_suffix, '#', $pair[2])"/>
									 </xsl:when>
									 <xsl:when test="Factor:builtin($strsrc)">
											<!--
												# Language domain reference.
											!-->
											<xsl:value-of select="ctx:python.builtin($strsrc)"/>
									 </xsl:when>
									 <xsl:otherwise>
											<xsl:value-of select="'#X-INVALID-REFERENCE'"/>
									 </xsl:otherwise>
									</xsl:choose>
								</xsl:otherwise>
							</xsl:choose>
						</xsl:otherwise>
					</xsl:choose>
				</xsl:otherwise>
			</xsl:choose>
		</func:result>
	</func:function>

	<func:function name="ctx:file">
		<xsl:param name="path"/>
		<xsl:param name="line"/>
		<xsl:variable name="tokens" select="fault:split('/', $path)"/>
		<func:result>
			<span class="path.directory"><xsl:value-of select="fault:join('/', $tokens[position()!=last()])"/>/</span>
			<span class="path.file.name"><xsl:value-of select="$tokens[last()][1]"/></span>
			<xsl:if test="$line">
				<span class="path.line.number"><xsl:value-of select="$line"/></span>
			</xsl:if>
		</func:result>
	</func:function>

	<func:function name="ctx:within.scope">
	 <xsl:param name="name"/>
		<func:result select="count($ctx.index[@key=$name]) > 0"/>
	</func:function>

	<func:function name="ctx:document">
		<xsl:param name="name"/>
		<xsl:variable name="path" select="$ctx.index[@key=$name]/text()"/>
		<xsl:if test="not($path)">
			<xsl:message>No such path: <xsl:value-of select="$name"/></xsl:message>
		</xsl:if>

		<xsl:choose>
		<xsl:when test="$path">
			<func:result select="document(concat('file://', $path))"/>
		</xsl:when>
		<xsl:otherwise>
			<func:result select="$path"/>
		</xsl:otherwise>
		</xsl:choose>
	</func:function>

	<func:function name="ctx:abstract">
		<xsl:param name="name"/>
		<xsl:variable name="factor" select="ctx:document($name)/f:factor"/>
		<xsl:variable name="fsection" select="$factor/f:*/f:doc/txt:section[not(@identifier)][1]"/>
		<xsl:variable name="fpara" select="$fsection/txt:paragraph[1]"/>

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

	<func:function name="ctx:local-abstract">
		<xsl:param name="name"/>
		<xsl:variable name="expr" select="//f:*[@xml:id=$name]"/>
		<xsl:variable name="fsection" select="$expr/f:doc/txt:section[not(@identifier)][1]"/>
		<xsl:variable name="fpara" select="$fsection/txt:paragraph[1]"/>

		<func:result select="string($fpara)"/>
	</func:function>

	<func:function name="ctx:has_test">
		<xsl:param name="id"/>

		<xsl:choose>
			<xsl:when test="/f:factor/f:test/t:report/t:context[@identifier=$id]">
				<func:result select="1=1"/>
			</xsl:when>
			<xsl:otherwise>
				<func:result select="1=0"/>
			</xsl:otherwise>
		</xsl:choose>
	</func:function>

	<!--Whether the factor has noted an error; test failure or load failure-->
	<func:function name="ctx:has_error">
		<xsl:param name="factor"/>
		<xsl:variable name="d" select="ctx:document($factor)/f:factor"/>

		<xsl:choose>
			<xsl:when test="$d/f:test//t:test[@impact=-1]">
				<func:result select="1=1"/>
			</xsl:when>
			<xsl:when test="$d//f:error">
				<func:result select="1=1"/>
			</xsl:when>
			<xsl:otherwise>
				<func:result select="1=0"/>
			</xsl:otherwise>
		</xsl:choose>
	</func:function>

	<func:function name="ctx:coverage">
		<xsl:param name="factor"/>
		<xsl:variable name="d" select="ctx:document($factor)/f:factor"/>
		<xsl:variable name="ntraversed" select="$d/f:coverage/@n-traversed"/>
		<xsl:variable name="ntraversable" select="$d/f:coverage/@n-traversable"/>
		<xsl:variable name="fraction" select="($ntraversed div $ntraversable)"/>

		<func:result select="$fraction * 100"/>
	</func:function>

	<func:function name="ctx:tests">
		<xsl:param name="factor"/>
		<xsl:variable name="project" select="/f:factor/f:context/@path"/>
		<xsl:variable name="pdoc" select="ctx:document($project)/f:factor"/>
		<xsl:variable name="tctx" select="$pdoc/f:test/t:report/t:context[@identifier=$factor]"/>
		<func:result select="$tctx"/>
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

	<xsl:template name="ctx.icon-image">
		<xsl:param name="icon"/>

		<xsl:variable name="il" select="string-length($icon)"/>

		<xsl:variable name="n1" select="substring($icon, 1, 1) = '&#60;'"/>
		<xsl:variable name="n2" select="substring($icon, $il, 1) = '>'"/>
		<xsl:variable name="inner" select="substring($icon, 2, $il - 2)"/>

		<xsl:choose>
			<xsl:when test="4 > $il">
				<xsl:value-of select="$icon"/>
			</xsl:when>
			<xsl:when test="$n1 = '&#38;' and $n2 = '>'">
				<img class="icon" src="{concat($inner, '/favicon.ico')}"/>
			</xsl:when>
			<xsl:otherwise>
				<xsl:value-of select="$icon"/>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>
</xsl:transform>
