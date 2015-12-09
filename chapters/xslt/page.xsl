<?xml version="1.0" encoding="utf-8"?>
<!--
 ! Transform documentation directory into presentable XHTML
 !-->
<xsl:transform version="1.0"
 xmlns="http://www.w3.org/1999/xhtml"
 xmlns:exsl="http://exslt.org/common"
 xmlns:str="http://exslt.org/strings"
 xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
 xmlns:f="https://fault.io/xml/factor"
	xmlns:e="https://fault.io/xml/eclectic"
 xmlns:ctx="https://fault.io/xml/factor#context"
 xmlns:df="https://fault.io/xml/factor#functions"
 xmlns:func="http://exslt.org/functions"
 extension-element-prefixes="func"
 exclude-result-prefixes="e xsl f ctx df str exsl">

	<!-- Everythin inside the site transforms should have precedence -->
 <xsl:import href="html.xsl"/>

 <xsl:param name="prefix"><xsl:text>/</xsl:text></xsl:param>
 <xsl:param name="long.args.limit" select="64"/>
	<xsl:param name="quote" select="'&#34;'"/>

 <func:function name="df:nlines">
  <xsl:param name="src"/>
  <func:result select="(number($src/@stop) - number($src/@start)) + 1"/>
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
	<xsl:template mode="function.index" match="node()"/>
	<xsl:template mode="toc" match="node()"/>

 <xsl:template mode="javascript.source.index" match="*">
	 <xsl:variable name="javascript_range"
			select="concat('[', f:source/@start, ',', f:source/@stop, ']')"/>
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

	<xsl:template mode="source.index" match="f:factor">
		<xsl:variable name="context" select="f:context"/>
		<div class="index.source">
			<xsl:for-each select="f:*[f:source]">
				<xsl:for-each select="f:source">
					<xsl:variable name="prefix" select="concat($context/@system.path, '/', ../@identifier, '/src/')"/>
					<xsl:variable name="relative" select="substring-after(@path, $prefix)"/>
					<xsl:variable name="rabsolute" select="substring-after(@path, $context/@system.path)"/>
						<div class="source-file">
							<a href="context.source/{$context/@project}{$rabsolute}">
								<xsl:choose>
									<xsl:when test="$relative">
										<xsl:value-of select="$relative"/>
									</xsl:when>
									<xsl:otherwise>
										<xsl:value-of select="$rabsolute"/>
									</xsl:otherwise>
								</xsl:choose>
							</a>
							<span class="line.count">(<xsl:value-of select="df:measure(.)"/>)</span>
						</div>
				</xsl:for-each>
			</xsl:for-each>
		</div>
	</xsl:template>
	<xsl:template mode="source.index" match="node()"/>

	<xsl:template mode="function.index" match="f:function[f:doc]">
		<xsl:variable name="src" select="f:source"/>
		<div class="index.function">
			<a href="{concat('#', @xml:id)}"><xsl:value-of select="@identifier"/></a>

			<xsl:if test="string(df:nlines($src)) != 'NaN'">
				<span class="line.count">
					(<xsl:value-of select="df:measure($src)"/>)
				</span>
			</xsl:if>
		</div>
	</xsl:template>

	<xsl:template mode="class.hierarchy" match="f:class">
		<xsl:variable name="this" select="@identifier"/>
		<xsl:variable name="src" select="f:source"/>
		<div class="index.class">
			<a href="{concat('#', @xml:id)}">
				<xsl:value-of select="@identifier"/>
			</a>

			<xsl:if test="string(df:nlines($src)) != 'NaN'">
				<span class="line.count">
					(<xsl:value-of select="df:measure($src)"/>)
				</span>
			</xsl:if>

			<xsl:apply-templates mode="class.hierarchy"
				select="../f:class[f:bases/f:reference[@factor=../../../@name and @name=$this]]">
				<xsl:sort order="ascending" select="@identifier"/>
			</xsl:apply-templates>
		</div>
	</xsl:template>

	<xsl:template mode="toc" match="e:section">
		<li>
			<a href="{concat('#', ctx:id(.))}">
				<xsl:value-of select="@identifier"/>
			</a>
			<xsl:if test="./e:section">
				<ol>
					<xsl:apply-templates mode="toc" select="e:section"/>
				</ol>
			</xsl:if>
		</li>
	</xsl:template>

	<xsl:template mode="toc" match="f:chapter">
		<ol>
			<xsl:apply-templates mode="toc" select="f:doc/e:section[@identifier]"/>
		</ol>
	</xsl:template>

	<xsl:template mode="total.toc" match="node()"/>
	<xsl:template mode="total.toc" match="e:section">
		<li>
			<a href="{concat(ancestor::f:factor/@name, '#', ctx:id(.))}">
				<xsl:value-of select="@identifier"/>
			</a>
			<xsl:if test="./e:section">
				<ol>
					<xsl:apply-templates mode="total.toc" select="e:section"/>
				</ol>
			</xsl:if>
		</li>
	</xsl:template>

	<xsl:template mode="total.toc" match="f:chapter">
		<ol>
			<xsl:apply-templates mode="total.toc" select="f:doc/e:section[@identifier]"/>
		</ol>
	</xsl:template>

 <xsl:template match="f:factor">
  <xsl:variable name="product" select="substring-before(@name, concat('.', @identifier))"/>
  <html>
   <head>
    <title><xsl:value-of select="f:module/@name"/> Documentation</title>
    <link rel="stylesheet" type="text/css" href="factor.css"/>
    <link rel="icon" href="{./@site}"/>

				<!-- syntax highlighting -->
				<link rel="stylesheet" type="text/css" href="prism.css"/>
				<script type="application/javascript" src="prism.js"/>

				<script type="application/javascript">
				 /* XXX: Might be wiser to just parse the original XML and access it. */
					var xml = null;
				 var documented_module = "<xsl:value-of select="@name"/>";
					var factor_name = "<xsl:value-of select="@identifier"/>";
					var mroindex = {
						<xsl:apply-templates mode="javascript.mro.index" select="/"/>
					}

					var srcindex = {
						<xsl:apply-templates mode="javascript.source.index" select="/"/>
					}

					var source = atob("<xsl:value-of
      select="normalize-space(f:*[f:source]/f:source/f:data/text())"/>").split('\n');
    </script>

				<script type="application/javascript" src="factor.js"/>
   </head>

   <body>
    <!-- dual paned -->
				<div id="content." class="content">
  			<xsl:variable name="subfactor" select="f:subfactor"/>
					<xsl:variable name="type"
						select="exsl:node-set('package')[$subfactor]|exsl:node-set('module')[not($subfactor)]"/>

					<div class="factor">
						<div class="title">
							<!-- it's not actually a keyword, but fills the role that keywords are used for -->
							<span class="icon"><xsl:value-of select="f:context/@icon"/></span>

							<xsl:if test="$product">
								<a href="{$product}">
									<span class="module-path"><xsl:value-of select="$product"/></span>
								</a>
								<span class="path-delimiter">.</span>
							</xsl:if>
							<a href=""><span class="identifier"><xsl:value-of select="@identifier"/></span></a>
						</div>
					</div>

					<!-- if there are subfactors, we're primarily concerned with navigation -->
					<xsl:if test="f:subfactor">
						<div class="navigation">
							<xsl:choose>
								<xsl:when test="@identifier = 'test'">
									<div class="subfactors">
										<xsl:apply-templates select="f:subfactor">
											<xsl:sort order="descending" select="starts-with(@identifier, 'test_')"/>
											<xsl:sort order="ascending" select="@identifier"/>
										</xsl:apply-templates>
									</div>
								</xsl:when>
								<xsl:when test="@identifier = 'documentation'">
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
							<!--
							<div class="cofactors">
								<xsl:for-each select="f:cofactor">
									<- units that are contained by the factor, but distinct ->
									<a href="{concat($product, '.', @identifier)}"><div><span class="identifier"><xsl:value-of select="@identifier"/></span></div></a>
								</xsl:for-each>
							</div>
							-->
						</div>
					</xsl:if>

					<xsl:for-each select="f:module">
						<div class="module">
							<xsl:apply-templates select="."/>
						</div>
					</xsl:for-each>

					<xsl:for-each select="f:chapter">
						<div class="chapter">
							<xsl:apply-templates select="./f:doc"/>
						</div>
					</xsl:for-each>
				</div>
				<div id="subject.description."></div> <!-- function source display -->

				<!-- subjection.description content when no hash is present. -->
				<!-- subject.default div is display: none in python.css; id is changed in
									hashchanged() -->
				<div id="subject.default.">
					<div class="source.index.">
					 <h2>Sources</h2>
						<xsl:apply-templates mode="source.index" select="."/>
					</div>

					<xsl:if test="f:chapter">
						<h2>Table of Contents</h2>
						<xsl:for-each select="f:chapter">
							<div class="toc">
								<xsl:apply-templates mode="toc" select="."/>
							</div>
						</xsl:for-each>
					</xsl:if>

					<xsl:if test="@identifier = 'documentation'">
						<h2>Table of Contents</h2>
						<ol>
							<xsl:for-each select="f:subfactor">
								<xsl:sort order="descending" select="@identifier = 'introduction'"/>
								<xsl:sort order="descending" select="@identifier = 'usage'"/>
								<xsl:sort order="ascending" select="@identifier"/>

								<xsl:variable name="chapter.path" select="concat(../@name, '.', @identifier)"/>
								<xsl:variable name="chapter" select="ctx:document($chapter.path)/f:factor/f:chapter"/>

								<li>
									<a href="{$chapter.path}"><span class="identifier"><xsl:value-of select="@identifier"/></span></a>
									<xsl:apply-templates mode="total.toc" select="$chapter"/>
								</li>
							</xsl:for-each>
						</ol>
					</xsl:if>

					<xsl:if test=".//f:function[f:doc]">
						<div class="function.index.">
							<h2>Functions</h2>
							<xsl:apply-templates mode="function.index" select=".//f:function">
								<xsl:sort order="ascending" select="@identifier"/>
							</xsl:apply-templates>
						</div>
					</xsl:if>

					<xsl:if test=".//f:class">
						<div class="class.hierarchy.">
							<!-- only select base classes; the template will manage the hierarchy -->
							<h2>Classes</h2>
							<xsl:apply-templates mode="class.hierarchy" select=".//f:class[f:bases/f:reference[@factor!=../../../@name]]">
								<xsl:sort order="ascending" select="@identifier"/>
							</xsl:apply-templates>
						</div>
					</xsl:if>

					<xsl:if test="@type = 'module' and .//f:import">
						<div class="imports.">
						 <h2>Runtime Dependencies</h2>
							<xsl:apply-templates select=".//f:import[@source='builtin']">
								<xsl:sort order="ascending" select="@identifier"/>
							</xsl:apply-templates>
							<xsl:apply-templates select=".//f:import[@source!='builtin']">
								<xsl:sort order="ascending" select="@identifier"/>
							</xsl:apply-templates>
						</div>
					</xsl:if>
				</div>
   </body>
  </html>
 </xsl:template>

</xsl:transform>
<!--
 ! vim: noet:sw=1:ts=1
 !-->
