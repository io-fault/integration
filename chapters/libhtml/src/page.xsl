<?xml version="1.0" encoding="utf-8"?>
<xsl:transform version="1.0"
	xmlns="http://www.w3.org/1999/xhtml"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	xmlns:exsl="http://exslt.org/common"
	xmlns:str="http://exslt.org/strings"
	xmlns:t="http://fault.io/xml/test"
	xmlns:txt="http://fault.io/xml/text"
	xmlns:f="http://fault.io/xml/fragments"
	xmlns:ctx="http://fault.io/xml/factor#context"
	xmlns:df="http://fault.io/xml/factor#functions"
	xmlns:func="http://exslt.org/functions"
	xmlns:fault="http://fault.io/xml/xpath"
	xmlns:Factor="http://fault.io/xpath#Factor"
	xmlns:xi="http://www.w3.org/2001/XInclude"
	extension-element-prefixes="func"
	exclude-result-prefixes="e xsl f ctx df str exsl fault">

	<xsl:import href="elements.xml"/>

	<xsl:param name="prefix"><xsl:text>/</xsl:text></xsl:param>
	<xsl:param name="long.args.limit" select="64"/>
	<xsl:param name="quote" select="'&#34;'"/>

	<func:function name="df:nlines">
		<xsl:param name="src"/>
		<func:result select="((number($src/@stop)+1) - number($src/@start))"/>
	</func:function>

	<func:function name="df:measure">
		<xsl:param name="src"/>
		<xsl:variable name="n" select="df:nlines($src)"/>
		<xsl:variable name="total.line.count" select="sum(ctx:factor($src)/f:*/f:source/@stop)"/>
		<xsl:variable name="p" select="($n div $total.line.count) * 100"/>

		<func:result>
			<xsl:value-of select="concat($n, ' lines ', format-number($p, '###.##'), '%')"/>
		</func:result>
	</func:function>

	<xsl:template mode="class.hierarchy" match="node()"/>
	<xsl:template mode="concept.index" match="node()"/>
	<xsl:template mode="toc" match="node()"/>

	<xsl:template mode="javascript.source.index" match="*">
		<xsl:variable name="untraversed" select="concat($quote, Factor:untraversed(), $quote)"/>
		<xsl:variable name="javascript_range"
			select="concat('[', f:source/@start, ',', f:source/@stop, ',', $untraversed, ']')"/>

		<xsl:value-of select="concat($quote, @xml:id, $quote, ':', $javascript_range, ',')"/>
	</xsl:template>

	<xsl:template mode="javascript.source.index" match="/">
		<xsl:apply-templates mode="javascript.source.index" select="//*[@xml:id and f:source/@start]"/>
	</xsl:template>

	<xsl:template mode="javascript.mro.index" match="f:reference">
		<xsl:variable name="name" select="concat($quote, @name, $quote)"/>
		<xsl:variable name="module" select="concat($quote, @module, $quote)"/>
		<xsl:variable name="source" select="concat($quote, @source, $quote)"/>

		<xsl:value-of select="concat('[', $source, ',', $module, ',', $name, ']', ',')"/>
	</xsl:template>

	<xsl:template mode="javascript.mro.index" match="/">
		<xsl:for-each select="//*[@xml:id and f:bases and f:order]">
			<xsl:value-of select="concat($quote, @xml:id, $quote)"/>
			<xsl:text>: </xsl:text>
			<xsl:text>[</xsl:text>
			<xsl:apply-templates mode="javascript.mro.index" select="f:order"/>
			<xsl:text>],</xsl:text>
		</xsl:for-each>
	</xsl:template>

	<xsl:template name="source.file">
		<xsl:param name="source"/>
		<xsl:variable name="context" select="$source/ancestor::f:factor/f:context"/>
		<xsl:variable name="prefix" select="concat($context/@system.path, '/', $source/@identifier, '/src/')"/>
		<xsl:variable name="relative" select="substring-after($source/@path, $prefix)"/>
		<xsl:variable name="rabsolute" select="substring-after($source/@path, $context/@system.path)"/>

		<xsl:value-of select="concat($context/@context,'/',$context/@project,$rabsolute)"/>
	</xsl:template>

	<xsl:template mode="source.index" match="f:factor">
		<xsl:variable name="ref.prefix" select="@depth"/>
		<xsl:variable name="context" select="f:context"/>

		<div class="if.vertical.sequence">
			<xsl:for-each select="f:*[f:source]">
				<xsl:for-each select="f:source">
					<xsl:variable name="prefix" select="concat($context/@system.path, '/', ../@identifier, '/src/')"/>
					<xsl:variable name="relative" select="substring-after(@path, $prefix)"/>
					<xsl:variable name="rabsolute" select="substring-after(@path, $context/@system.path)"/>
						<a href="{$ref.prefix}.source/{$context/@name}{$context/@project}{$rabsolute}">
							<div class="if.item">
								<div class="icon">📄</div>
								<div class="label">
									<xsl:choose>
										<xsl:when test="$relative">
											<xsl:value-of select="$relative"/>
										</xsl:when>
										<xsl:otherwise>
											<xsl:value-of select="$rabsolute"/>
										</xsl:otherwise>
									</xsl:choose>
									<span class="superscript">
										<xsl:value-of select="df:measure(.)"/>
									</span>
								</div>
								<div class="abstract">
									<!--last modified & size?-->
								</div>
							</div>
						</a>
				</xsl:for-each>
			</xsl:for-each>
		</div>
	</xsl:template>

	<xsl:template mode="source.index" match="node()"/>

	<xsl:template mode="test.summary" match="f:test">
		<xsl:apply-templates mode="test.summary" select="t:report"/>
	</xsl:template>

	<xsl:template mode="test.summary" match="t:report">
		<div class="test-report">
			<div class="if.vertical.sequence">
				<xsl:apply-templates mode="test.summary" select="t:context">
					<xsl:sort order="descending" select="count(t:test[@impact=-1])"/>
					<xsl:sort select="not(@identifier)"/>
					<xsl:sort select="@identifier"/>
				</xsl:apply-templates>
			</div>
		</div>
	</xsl:template>

	<xsl:template mode="test.summary" match="t:context">
		<xsl:variable name="f.count" select="count(t:test[@impact=-1])"/>
		<xsl:variable name="p.count" select="count(t:test[@impact=1])"/>
		<xsl:variable name="z.count" select="count(t:test[@impact=0])"/>
		<xsl:variable name="duration" select="sum(t:test/@duration)"/>

		<a href="{concat(@identifier, $reference_suffix)}">
			<div class="if.item">
				<div class="icon">
					<xsl:choose>
						<xsl:when test="$f.count > 0">
							<xsl:text>⛔️</xsl:text>
						</xsl:when>
						<xsl:otherwise>
							<xsl:text>✅</xsl:text>
						</xsl:otherwise>
					</xsl:choose>
				</div>

				<div class="label">
					<span class="identifier"><xsl:value-of select="@identifier"/></span>
					<span style="margin-left: 2px;" class="superscript">
						<xsl:text>[</xsl:text>
						<span class="test.fail"><xsl:value-of select="$f.count"/></span>
						<xsl:text>:</xsl:text>
						<span class="test.pass"><xsl:value-of select="$p.count"/></span>
						<xsl:text>:</xsl:text>
						<span class="test.skip"><xsl:value-of select="$z.count"/></span>
						<xsl:text>/</xsl:text>
						<span class="test.count">
							<xsl:value-of select="$f.count + $p.count + $z.count"/>
						</span>
						<xsl:text>]</xsl:text>
					</span>
				</div>
				<div class="abstract">
					<xsl:copy-of select="ctx:duration(Factor:duration($duration))"/>
				</div>
			</div>
		</a>
	</xsl:template>

	<xsl:template mode="concept.index" match="f:*[@identifier]">
		<xsl:variable name="src" select="f:source"/>
		<a href="{concat('#', @xml:id)}">
			<div class="if.item">
				<div class="label">
					<xsl:value-of select="@identifier"/>
					<span class="superscript">
						<xsl:if test="string(df:nlines($src)) != 'NaN'">
							<xsl:value-of select="df:measure($src)"/>
						</xsl:if>
					</span>
				</div>

				<div class="abstract">
					<xsl:copy-of select="ctx:local-abstract(@xml:id)"/>
				</div>
			</div>
		</a>
	</xsl:template>

	<xsl:template mode="class.hierarchy" match="f:class">
		<xsl:variable name="this" select="@identifier"/>
		<xsl:variable name="src" select="f:source"/>
		<xsl:variable name="subclasses"
			select="../f:class[f:bases/f:reference[@factor=../../../@name and @name=$this]]"/>

		<a href="{concat('#', @xml:id)}">
			<div class="if.item">
				<div class="label">
					<xsl:value-of select="@identifier"/>
					<span class="superscript">
						<xsl:if test="string(df:nlines($src)) != 'NaN'">
							<xsl:value-of select="df:measure($src)"/>
						</xsl:if>
					</span>
				</div>

				<div class="abstract">
					<xsl:copy-of select="ctx:local-abstract(@xml:id)"/>
				</div>
			</div>
		</a>

		<xsl:if test="$subclasses">
			<div class="if.vertical.sequence">
				<xsl:apply-templates mode="class.hierarchy" select="$subclasses">
					<xsl:sort order="ascending" select="@identifier"/>
				</xsl:apply-templates>
			</div>
		</xsl:if>
	</xsl:template>

	<xsl:template mode="toc" match="txt:section">
		<li>
			<a href="{concat('#', ctx:id(.))}">
				<xsl:value-of select="@identifier"/>
			</a>
			<xsl:if test="./txt:section">
				<ol>
					<xsl:apply-templates mode="toc" select="txt:section"/>
				</ol>
			</xsl:if>
		</li>
	</xsl:template>

	<xsl:template mode="toc" match="f:chapter">
		<ol>
			<xsl:apply-templates mode="toc" select="f:doc/txt:section[@identifier]"/>
		</ol>
	</xsl:template>

	<xsl:template mode="total.toc" match="node()"/>
	<xsl:template mode="total.toc" match="txt:section">
		<li>
			<a href="{concat(ancestor::f:factor/@name, $reference_suffix, '#', ctx:id(.))}">
				<xsl:value-of select="@identifier"/>
			</a>
			<xsl:if test="./txt:section">
				<ol>
					<xsl:apply-templates mode="total.toc" select="txt:section"/>
				</ol>
			</xsl:if>
		</li>
	</xsl:template>

	<xsl:template mode="total.toc" match="f:chapter">
		<ol>
			<xsl:apply-templates mode="total.toc" select="f:doc/txt:section[@identifier]"/>
		</ol>
	</xsl:template>

	<xsl:template match="f:factor">
		<xsl:variable name="product" select="substring-before(@name, concat('.', @identifier))"/>
		<xsl:variable name="context.cache" select="Factor:cache()"/>
		<xsl:variable name="depth" select="/f:factor/@depth"/>
		<xsl:variable name="path.prefix">
			<!--
				# Empty if no depth attribute.
			!-->
			<xsl:choose>
				<xsl:when test="$depth"><xsl:value-of select="$depth"/></xsl:when>
				<xsl:otherwise><xsl:text></xsl:text></xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:variable name="default.language" select="./f:module/@language[position()=1]"/>

		<html>
			<head>
				<title><xsl:value-of select="f:module/@name"/> <xsl:value-of select="$title_suffix"/></title>
				<link rel="stylesheet" type="text/css" href="{$path.prefix}factor.css"/>
				<link rel="icon" href="{./@site}"/>

				<script type="application/javascript">
					var xml = null;
					<xsl:choose>
					<xsl:when test="$default.language">
					var default_language = "<xsl:value-of select="$default.language[position()=1]"/>";
					</xsl:when>
					<xsl:otherwise>
					var default_language = "python";
					</xsl:otherwise>
					</xsl:choose>
					var documented_module = "<xsl:value-of select="@name"/>";
					var factor_name = "<xsl:value-of select="@identifier"/>";

					var factor_source =
					<xsl:text>&#34;</xsl:text>
					<xsl:call-template name="source.file">
						<xsl:with-param name="source" select="f:module/f:source"/>
					</xsl:call-template>
					<xsl:text>&#34;;</xsl:text>

					var mroindex = {
						<xsl:apply-templates mode="javascript.mro.index" select="/"/>
					}

					var srcindex = {
						<xsl:apply-templates mode="javascript.source.index" select="/"/>
					}

					var source = atob(
						<xsl:text>&#34;</xsl:text>
						<xsl:value-of
							select="normalize-space(f:*[f:source]/f:source/f:data/text())"/>
						<xsl:text>&#34;</xsl:text>
					).split('\n');
				</script>
				<script type="application/javascript" src="{$path.prefix}factor.js"/>
			</head>

			<body>
				<div class="factor">
					<div class="title">
						<span class="icon">
							<xsl:call-template name="ctx.icon-image">
								<xsl:with-param name="icon" select="f:context/@icon"/>
							</xsl:call-template>
						</span>

						<xsl:if test="/f:factor/f:context/@type = 'corpus'">
							<a href="">
								<span class="identifier">
									<xsl:value-of select="/f:factor/f:context/@name"/>
									<xsl:text> Software Corpus</xsl:text>
								</span>
							</a>
						</xsl:if>

						<xsl:if test="$product">
								<xsl:for-each select="fault:traverse('.', $product)">
									<a href="{$depth}{ctx:absolute(string(./path))}">
										<span class="module-path"><xsl:value-of select="./token/text()[1]"/></span>
									</a>
									<span class="path-delimiter">.</span>
								</xsl:for-each>
						</xsl:if>

						<a>
							<xsl:attribute name="href">
								<xsl:choose>
									<xsl:when test="$depth">
										<xsl:value-of select="$depth"/>
										<xsl:value-of select="/f:factor/@name"/>
									</xsl:when>
									<xsl:otherwise>
										<!--
											# Nothing for self pointers to the same factor.
										!-->
										<xsl:value-of select="''"/>
									</xsl:otherwise>
								</xsl:choose>
							</xsl:attribute>

							<span class="identifier">
								<xsl:value-of select="@identifier"/>
							</span>
						</a>
						<xsl:if test="$depth">
							<xsl:text>/</xsl:text>
							<a href="">
								<span class="fraction">
									<xsl:value-of select="/f:factor/@path"/>
								</span>
							</a>
						</xsl:if>
					</div>
					<div style="display:none" class="index.reference">
						<a href="#index."><span class="tab">Index</span></a>
						<a href="#source..index"><span class="tab">Sources</span></a>
						<a href="#functions..index"><span class="tab">Functions</span></a>
						<a href="#class..index"><span class="tab">Classes</span></a>
						<a href="#struct..index"><span class="tab">Structures</span></a>
					</div>
				</div>

				<div id="content." class="pane.">
					<xsl:variable name="test.package" select="/f:factor/@type = 'tests'"/>
					<xsl:variable name="prefix" select="concat(/f:factor/@name, '.')"/>

					<xsl:if test="/f:factor/@type != 'chapter'">
						<div class="doc">
							<xsl:apply-templates
								select="/f:factor/f:module/f:doc/txt:section[not(@identifier) or @identifier!='Properties']"/>
						</div>
					</xsl:if>

					<!--
						# Project Package displays test summary
					!-->
					<xsl:if test="$test.package and /f:factor/f:test[t:*]">
						<div style="margin: 1cm;" class="project..tests">
							<xsl:apply-templates mode="test.summary" select="/f:factor/f:test"/>
						</div>
					</xsl:if>

					<!--
						# If there are subfactors, it effects navigation.
					!-->
					<xsl:if test="f:subfactor">
						<div class="navigation">
							<div class="if.vertical.sequence">
								<xsl:choose>
									<xsl:when test="$test.package">
										<div class="subfactors">
											<!--
												# Show test status of subfactors.
											!-->
											<xsl:apply-templates select="f:subfactor[not(ctx:has_test(concat($prefix, @identifier)))]">
												<xsl:sort order="ascending" select="@identifier"/>
											</xsl:apply-templates>
										</div>
									</xsl:when>
									<xsl:when test="/f:factor/@type = 'documentation'">
										<div class="subfactors">
											<xsl:apply-templates select="f:subfactor">
												<xsl:sort order="descending" select="@identifier = 'introduction'"/>
												<xsl:sort order="descending" select="@identifier = 'usage'"/>
												<xsl:sort order="ascending" select="@identifier"/>
												<xsl:sort order="ascending" select="@identifier = 'context.txt'"/>
											</xsl:apply-templates>
										</div>
									</xsl:when>
									<xsl:otherwise>
										<div class="subfactors">
											<xsl:apply-templates select="f:subfactor">
												<xsl:sort order="descending" select="@identifier = 'documentation'"/>
												<xsl:sort order="descending" select="@identifier = 'test'"/>
												<xsl:sort order="descending" select="@identifier = 'bin'"/>
												<xsl:sort order="descending" select="@identifier = 'library'"/>
												<xsl:sort order="descending" select="starts-with(@identifier, 'lib')"/>
												<xsl:sort order="ascending" select="@identifier = 'core'"/>
												<xsl:sort order="ascending" select="@identifier = 'abstract'"/>
												<xsl:sort order="ascending" select="@identifier"/>
											</xsl:apply-templates>
										</div>
									</xsl:otherwise>
								</xsl:choose>
							</div>
						</div>
					</xsl:if>

					<xsl:for-each select="f:module">
						<div class="module">
							<xsl:apply-templates select="."/>
						</div>
					</xsl:for-each>

					<xsl:for-each select="f:chapter">
						<div class="chapter">
							<xsl:apply-templates mode="chapter" select="./f:doc"/>
						</div>
					</xsl:for-each>

					<div id="index." class="index">
						<div class="title">Index</div>

						<div id="source..index" class="factor..sources">
							<div class="title">Sources</div>
							<xsl:apply-templates mode="source.index" select="."/>
						</div>

						<xsl:if test="@type = 'module' and .//f:import">
							<div id="import..index" class="factor..imports">
								<div class="title">Imports</div>
								<div class="if.vertical.sequence">
									<xsl:apply-templates select=".//f:import">
										<xsl:sort order="ascending" select="ctx:within.scope(@name)"/>
										<xsl:sort order="ascending" select="@name"/>
									</xsl:apply-templates>
								</div>
								</div>
						</xsl:if>

						<xsl:if test=".//f:function[f:doc]">
							<div id="function..index" class="factor..functions">
								<div class="title">Functions</div>
								<div class="if.vertical.sequence">
								<xsl:apply-templates mode="concept.index" select=".//f:function[f:doc]">
									<xsl:sort order="ascending" select="@identifier"/>
								</xsl:apply-templates>
								</div>
							</div>
						</xsl:if>

						<xsl:if test=".//f:structure[f:doc]">
							<div id="structure..index" class="factor..structures">
								<div class="title">Structures</div>
								<div class="if.vertical.sequence">
								<xsl:apply-templates mode="concept.index" select=".//f:structure[f:doc]">
									<xsl:sort order="ascending" select="@identifier"/>
								</xsl:apply-templates>
								</div>
							</div>
						</xsl:if>

						<xsl:if test=".//f:class">
							<div id="class..index" class="factor..classes">
								<div class="title">Classes</div>
								<div class="if.vertical.sequence">
								<xsl:apply-templates mode="class.hierarchy" select=".//f:class[f:bases/f:reference[@factor!=../../../@name]]">
									<xsl:sort order="ascending" select="@identifier"/>
								</xsl:apply-templates>
								</div>
							</div>
						</xsl:if>

						<xsl:if test="@identifier = 'documentation'">
							<div id="section..index" class="factor..sections">
							<div class="title">Table of Contents</div>
							<ol>
								<xsl:for-each select="f:subfactor">
									<xsl:sort order="descending" select="@identifier = 'introduction'"/>
									<xsl:sort order="descending" select="@identifier = 'usage'"/>
									<xsl:sort order="ascending" select="@identifier"/>

									<xsl:variable name="chapter.path" select="concat(../@name, '.', @identifier)"/>
									<xsl:variable name="chapter" select="ctx:document($chapter.path)/f:factor/f:chapter"/>

									<li>
										<a href="{$chapter.path}{$reference_suffix}">
											<span class="identifier"><xsl:value-of select="@identifier"/></span>
										</a>
										<xsl:apply-templates mode="total.toc" select="$chapter"/>
									</li>
								</xsl:for-each>
							</ol>
							</div>
						</xsl:if>
					</div>
				</div>

				<div class="pane." id="log."></div>
			</body>
		</html>
	</xsl:template>
</xsl:transform>
