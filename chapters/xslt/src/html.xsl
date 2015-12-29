<?xml version="1.0" encoding="utf-8"?>
<!--
 ! Transform extracted project documentation into XHTML
 ! Signatures hide keyword arguments that are not annotated.
 !-->
<xsl:transform version="1.0"
 xmlns="http://www.w3.org/1999/xhtml"
 xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
 xmlns:xl="http://www.w3.org/1999/xlink"
 xmlns:set="http://exslt.org/sets"
 xmlns:str="http://exslt.org/strings"
 xmlns:exsl="http://exslt.org/common"
 xmlns:f="https://fault.io/xml/factor"
 xmlns:e="https://fault.io/xml/eclectic"
 xmlns:py="https://fault.io/xml/python"
 xmlns:df="https://fault.io/xml/factor#functions"
 xmlns:ctx="https://fault.io/xml/factor#context"
 xmlns:func="http://exslt.org/functions"
 xmlns:l="https://fault.io/xml/literals"
 extension-element-prefixes="func"
 exclude-result-prefixes="set str exsl func xl xsl py e f df ctx">

 <xsl:param name="prefix"><xsl:text>/</xsl:text></xsl:param>
 <xsl:param name="long.args.limit" select="64"/>
 <xsl:param name="bytes.limit" select="256"/>

 <xsl:param name="python.version" select="'3'"/>
 <xsl:param name="python.docs" select="concat('https://docs.python.org/', $python.version, '/library/')"/>

 <!-- arguably configuration -->
 <xsl:variable name="functions_title" select="'functions'"/>
 <xsl:variable name="classes_title" select="'classes'"/>
 <xsl:variable name="methods_title" select="'methods'"/>
 <xsl:variable name="static_methods_title" select="'static methods'"/>
 <xsl:variable name="class_methods_title" select="'class methods'"/>
 <xsl:variable name="properties_title" select="'properties'"/>
 <xsl:variable name="class_data_title" select="'class data'"/>
 <xsl:variable name="data_title" select="'data'"/>
 <xsl:variable name="imports_title" select="'imports'"/>

 <xsl:variable name="arg.sep"><span class="sequence-delimiter">,</span></xsl:variable>
 <xsl:variable name="arg.assignment"><span class="assignment">=</span></xsl:variable>

 <xsl:template match="l:*">
  <xsl:variable name="n" select="string(local-name())"/>
  <span class="xml.literal">0<xsl:value-of select="$n"/></span>
 </xsl:template>

 <xsl:template name="admonition">
  <!-- if there is no identified ancestor, it's probably the root object (module) -->
  <xsl:param name="severity"/>
  <xsl:param name="title"/>
  <xsl:param name="content"/>

  <div class="admonition-{$severity}">
   <table>
    <tr>
     <td>
      <span class="admonition.icon"/>
     </td>
     <td>
      <span class="admonition.severity"><xsl:value-of select="$severity"/>: <xsl:value-of select="$title"/></span>
     </td>
    </tr>
    <tr>
     <td/>
     <td>
      <div class="admonition.content">
       <xsl:copy-of select="$content"/>
      </div>
     </td>
    </tr>
   </table>
  </div>
 </xsl:template>

 <func:function name="f:inherit.docs">
  <xsl:param name="class"/>

  <xsl:variable name="section" select="$class/f:doc/e:section[position()=1 and last()=1]"/>
  <xsl:variable name="para" select="$section/e:paragraph[position()=1 and last()=1]"/>
  <xsl:variable name="ref" select="$para/e:reference[position()=1 and last()=1]"/>

  <func:result>
   <xsl:choose>
    <!-- first and only reference/paragraph/section -->
    <xsl:when test="$ref">
     <xsl:value-of select="string($ref/@source)"/>
    </xsl:when>
    <xsl:otherwise>
     <xsl:value-of select="''"/>
    </xsl:otherwise>
   </xsl:choose>
  </func:result>
 </func:function>

 <func:function name="df:tag">
  <xsl:param name="text"/>
  <xsl:param name="type"/>
  <xsl:param name="reference" select="false"/>

  <func:result>
	  <span class="tag"><span class="text"><xsl:value-of select="$text"/></span><span class="type"><xsl:value-of select="$type"/></span></span>
  </func:result>
 </func:function>

	<xsl:template match="f:context">
   <a href="{@identity}"><xsl:value-of select="@project"/></a>
   <xsl:text> </xsl:text>
   <a href="{@contact}"><xsl:value-of select="@controller"/></a>
   <!-- <xsl:copy-of select="df:tag(@fork, 'fork')"/> -->
	</xsl:template>

 <func:function name="df:reference">
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
     <!-- Same site (document collection) -->
     <xsl:value-of select="concat($element/@factor, '#', $element/@name)"/>
    </xsl:otherwise>
   </xsl:choose>
  </func:result>
 </func:function>

 <func:function name="df:qname">
  <xsl:param name="element" select="."/>

  <func:result>
   <xsl:value-of select="concat($element/@factor, '.', $element/@name)"/>
  </func:result>
 </func:function>

 <xsl:template match="e:emphasis[@weight=1]">
  <span class="eclectic.emphasis"><xsl:value-of select="text()"/></span>
 </xsl:template>

 <xsl:template match="e:emphasis[@weight=2]">
  <span class="eclectic.emphasis.heavy"><xsl:value-of select="text()"/></span>
 </xsl:template>

 <xsl:template match="e:emphasis[@weight>2]">
  <span class="eclectic.emphasis.excessive"><xsl:value-of select="text()"/></span>
 </xsl:template>

 <xsl:template match="e:literal">
  <!-- inline literal -->
  <xsl:choose>
   <xsl:when test="not(@qualifications)">
    <code class="language-python"><xsl:value-of select="text()"/></code>
   </xsl:when>
   <xsl:otherwise>
    <span class="{concat('quals', @qualifications)}"><xsl:value-of select="text()"/></span>
   </xsl:otherwise>
  </xsl:choose>
 </xsl:template>

 <xsl:template match="e:literals">
  <xsl:variable name="start" select="e:line[text()][1]"/>
  <xsl:variable name="stop" select="e:line[text()][last()]"/>
  <xsl:variable name="lang" select="substring-after(@type, '/pl/')"/>

  <!-- the source XML may contain leading and trailing empty lines -->
  <!-- the selection filters empty e:line's on the edges -->
  <div class="eclectic.literals">
   <pre class="language-{$lang}">
    <code class="language-{$lang}">
     <xsl:for-each
      select="e:line[.=$start or .=$stop or (preceding-sibling::e:*[.=$start] and following-sibling::e:*[.=$stop])]">
      <xsl:value-of select="concat(text(), '&#10;')"/>
     </xsl:for-each>
    </code>
   </pre>
  </div>
 </xsl:template>

 <xsl:template match="e:dictionary">
  <dl class="eclectic">
   <xsl:for-each select="e:item">
    <xsl:variable name="ref" select="ctx:prepare-id(ctx:id(.))"/>
    <dt id="{$ref}"><xsl:apply-templates select="e:key/e:*|e:key/text()"/><a href="#{$ref}" class="dkn"/></dt>
    <dd><xsl:apply-templates select="e:value/e:*"/></dd>
   </xsl:for-each>
  </dl>
 </xsl:template>

 <xsl:template match="e:sequence">
  <ol class="eclectic">
   <xsl:for-each select="e:item">
    <li><xsl:apply-templates select="e:*|text()"/></li>
   </xsl:for-each>
  </ol>
 </xsl:template>

 <xsl:template match="e:set">
  <ul class="eclectic">
   <xsl:for-each select="e:item">
    <li><xsl:apply-templates select="e:*|text()"/></li>
   </xsl:for-each>
  </ul>
 </xsl:template>

 <xsl:template match="e:paragraph">
  <p><xsl:apply-templates select="node()"/></p>
 </xsl:template>

 <xsl:template match="e:reference">
  <xsl:variable name="address" select="ctx:reference(.)"/>
  <a class="eclectic.reference" href="{$address}"><xsl:value-of select="@source"/><span class="ern"/></a>
 </xsl:template>

 <xsl:template match="e:section[@identifier]">
  <!-- if there is no identified ancestor, it's probably the root object (module) -->
  <xsl:variable name="id" select="ctx:id(.)"/>

  <div id="{$id}" class="section">
   <div class="section.title">
    <a class="eclectic.reference" href="{concat('#', $id)}">
     <xsl:value-of select="@identifier"/>
    </a>
    <!-- Provide context links for subsections -->
    <xsl:if test="ancestor::e:section">
     <xsl:variable name="super" select="ancestor::e:section"/>
     <a href="{concat('#', ctx:id($super))}" class="supersection">
      [<xsl:value-of select="$super/@identifier"/>]
     </a>
    </xsl:if>
   </div>
   <xsl:apply-templates select="e:*"/>
  </div>
 </xsl:template>

 <xsl:template match="e:section[not(@identifier)]">
  <!-- Don't include the div if the leading section is empty -->
  <xsl:if test="e:*/node()">
   <div id="{ctx:id(.)}"><xsl:apply-templates select="e:*"/></div>
  </xsl:if>
 </xsl:template>

 <xsl:template match="e:admonition">
  <!-- if there is no identified ancestor, it's probably the root object (module) -->
  <div class="admonition-{@severity}">
   <table>
    <tr>
     <td>
      <span class="admonition.icon"/>
     </td>
     <td>
      <span class="admonition.severity"><xsl:value-of select="@severity"/>: <xsl:value-of select="@identifier"/></span>
     </td>
    </tr>
    <tr>
     <td/>
     <td>
      <div class="admonition.content">
       <xsl:apply-templates select="e:*"/>
      </div>
     </td>
    </tr>
   </table>
  </div>
 </xsl:template>

 <xsl:template match="f:doc">
  <div class="doc"><xsl:apply-templates select="e:*"/></div>
 </xsl:template>

 <xsl:template match="f:instructions">
  <div class="frame.instructions python">
   <pre><xsl:value-of select="text()"/></pre>
  </div>
 </xsl:template>

 <xsl:template match="f:line[@absolute]">
  <span class="source.line.focus">
   <xsl:value-of select="./text()"/>
   <xsl:text>&#10;</xsl:text>
  </span>
 </xsl:template>

 <xsl:template match="f:line">
  <span class="source.line">
   <xsl:value-of select="./text()"/>
   <xsl:text>&#10;</xsl:text>
  </span>
 </xsl:template>

 <xsl:template match="f:frame">
  <xsl:variable name="identifier" select="(@factor|@module)[1]"/>
  <xsl:variable name="sym" select="@symbol"/>
  <xsl:variable name="module_body" select="@symbol = '&lt;module&gt;'"/>
  <xsl:variable name="pos" select="position()"/>
  <xsl:variable name="file" select="string(f:source/@file)"/>
  <xsl:variable name="line" select="f:source/f:line[@absolute]/@absolute"/>

  <li class="python.frame">
   <div class="frame-header">
    <xsl:choose>
     <xsl:when test="@factor">
      <xsl:variable name="e" select="ctx:element.from.source(@factor, f:source/@first)"/>
      <xsl:variable name="eid" select="ctx:id($e)"/>
      <xsl:variable name="fact" select="$e/ancestor::f:module/@name"/>

      <!-- case where code object is module body vs function/method -->
      <xsl:choose>
       <xsl:when test="not($module_body)">
        <a href="{$fact}{$reference_suffix}#{$eid}">
         <xsl:value-of select="@factor"/>
         <xsl:text>.</xsl:text>

         <span class="identifier">
          <xsl:value-of select="$eid"/>
         </span>
        </a>
       </xsl:when>
       <xsl:otherwise>
        <a href="{@factor}{$reference_suffix}">
         <span class="identifier">
          <xsl:value-of select="@factor"/>
         </span>
        </a>
       </xsl:otherwise>
      </xsl:choose>
     </xsl:when>

     <xsl:when test="$identifier = '__main__'">
     </xsl:when>

     <xsl:otherwise>
      <xsl:value-of select="$identifier"/>
      <xsl:text>.</xsl:text>
      <xsl:value-of select="$sym"/>
     </xsl:otherwise>
    </xsl:choose>

    <xsl:text> </xsl:text>
    [<xsl:copy-of select="ctx:file($file, $line)"/>]
   </div>
   <div
     ondblclick="toggle_collapsed(event)"
     class="frame.source collapsed"><!-- collapsed by default to focus lines -->
    <pre>
     <code data-start="{f:source/@start}">
      <xsl:apply-templates select="f:source/f:line"/>
     </code>
    </pre>
   </div>
   <xsl:apply-templates select="f:context"/>
   <xsl:apply-templates select="f:instructions"/>
  </li>
 </xsl:template>

 <xsl:template match="f:traceback">
  <div class="python.traceback">
   <ol class="frames">
    <xsl:apply-templates select="f:frame"/>
   </ol>
  </div>
 </xsl:template>

 <xsl:template match="f:exception">
  <div class="python.exception">
   <a href="{df:reference(@type)}">
   </a>
   <xsl:call-template name="admonition">
    <xsl:with-param name="severity" select="'ERROR'"/>
    <xsl:with-param name="title" select="@type"/>
    <xsl:with-param name="content" select="string(f:message/text())"/>
   </xsl:call-template>
   <xsl:apply-templates select="f:traceback"/>

   <!-- exception chains -->
   <xsl:for-each select="f:exception">
    <div class="exception.{./@identifier}">
     <xsl:apply-templates select="."/>
    </div>
   </xsl:for-each>
  </div>
 </xsl:template>

 <xsl:template match="f:error">
  <xsl:apply-templates select="f:exception"/>
 </xsl:template>

 <xsl:template mode="python.inline.data" match="f:none">
  <span class="python.type.none"><xsl:value-of select="'None'"/></span>
 </xsl:template>

 <xsl:template mode="python.inline.data" match="f:true">
  <span class="python.type.bool"><xsl:value-of select="'True'"/></span>
 </xsl:template>

 <xsl:template mode="python.inline.data" match="f:false">
  <span class="python.type.bool"><xsl:value-of select="'False'"/></span>
 </xsl:template>

 <xsl:template mode="python.inline.data" match="f:integer">
  <span class="python.type.integer"><xsl:value-of select="text()"/></span>
 </xsl:template>

 <xsl:template mode="python.inline.data" match="f:real">
  <span class="python.type.real"><xsl:value-of select="text()"/></span>
 </xsl:template>

 <xsl:template mode="python.inline.data" match="f:bytes">
  <xsl:choose>
   <xsl:when test="@sample">
    <span class="python.type.bytes"><xsl:value-of select="@sample"/></span>
   </xsl:when>
   <xsl:when test="string-length(text()) > 256">
    <span class="python.type.bytes">[<xsl:value-of select="string-length(text())"/> bytes]</span>
   </xsl:when>
   <xsl:otherwise>
    <span class="python.type.bytes"><xsl:value-of select="text()"/></span>
   </xsl:otherwise>
  </xsl:choose>
 </xsl:template>

 <xsl:template mode="python.inline.data" match="f:string">
  <span class="python.type.string"><xsl:apply-templates select="node()"/></span>
 </xsl:template>

 <xsl:template mode="python.inline.data" match="f:list">
  <span class="python.list.open">[</span>
  <xsl:apply-templates mode="python.inline.data" select="f:*"/>
  <span class="python.list.close">]</span>
 </xsl:template>

 <xsl:template mode="python.inline.data" match="f:tuple">
  <span class="python.tuple.open">(</span>
  <xsl:choose>
   <xsl:when test="f:*">
    <div class="python.tuple">
     <xsl:for-each select="f:*">
      <xsl:apply-templates mode="python.inline.data" select="."/>
      <span class="sequence-delimiter">,</span>
     </xsl:for-each>
    </div>
   </xsl:when>
   <xsl:otherwise>
    <span class="python.empty.tuple"/>
   </xsl:otherwise>
  </xsl:choose>
  <span class="python.tuple.close">)</span>
 </xsl:template>

 <xsl:template mode="python.inline.data" match="f:item">
  <span class="python.dictionary.item">
   <span class="python.dictionary.key"><xsl:apply-templates mode="python.inline.data" select="f:*[position()=1]"/></span>
   <xsl:text>: </xsl:text>
   <span class="python.dictionary.value"><xsl:apply-templates mode="python.inline.data" select="f:*[position()=2]"/></span>
   <xsl:text>,</xsl:text>
   <br/>
  </span>
 </xsl:template>

 <xsl:template mode="python.inline.data" match="f:object">
  <xsl:apply-templates select="f:error"/>
  <xsl:apply-templates select="f:*[local-name()!='error']" mode="python.inline.data"/>
 </xsl:template>

 <xsl:template mode="python.inline.data" match="f:dictionary">
  <span class="python.dictionary.open">{</span><br/>
  <xsl:apply-templates select="f:*" mode="python.inline.data"/>
  <br/><span class="python.dictionary.close">}</span>
 </xsl:template>

 <xsl:template mode="python.inline.data" match="f:reference">
  <a href="{df:reference(.)}"><span class="reference"><xsl:value-of select="@name"/></span></a>
 </xsl:template>

 <xsl:template name="method">
  <xsl:param name="element"/>

  <xsl:variable name="name" select="$element/@identifier"/>
  <xsl:variable name="path" select="$element/@xml:id"/>
  <xsl:variable name="ismethod" select="($element/..)[local-name()='class']"/>
  <xsl:variable name="includedef" select="not($ismethod)"/>
  <xsl:variable name="context" select="$element/ancestor::f:*[@identifier][1]"/>
  <xsl:variable name="leading.name" select="$context/@identifier"/>
  <xsl:variable name="element.name" select="local-name($element)"/>

  <div>
   <xsl:choose>
    <xsl:when test="$ismethod">
     <xsl:choose>
      <!-- Distinction is made as we normally want to hide these -->
      <xsl:when test="$name = '__repr__'">
       <xsl:attribute name="class"><xsl:value-of select="'python-protocol-method'"/></xsl:attribute>
      </xsl:when>
      <xsl:when test="$name = '__str__'">
       <xsl:attribute name="class"><xsl:value-of select="'python-protocol-method'"/></xsl:attribute>
      </xsl:when>
      <xsl:otherwise>
       <xsl:attribute name="class"><xsl:value-of select="$element.name"/></xsl:attribute>
      </xsl:otherwise>
     </xsl:choose>
    </xsl:when>

    <xsl:otherwise>
     <xsl:attribute name="class"><xsl:value-of select="$element.name"/></xsl:attribute>
    </xsl:otherwise>
   </xsl:choose>

   <xsl:attribute name="id"><xsl:value-of select="$element/@xml:id"/></xsl:attribute>

   <div class="title">
    <a href="#{ctx:id($context)}">
     <span class="identity-context">
      <xsl:value-of select="$leading.name"/>
     </span>
    </a>
    <span class="path-delimiter">.</span>
    <a href="{concat('#',$element/@xml:id)}"><span class="identifier"><xsl:value-of select="$name"/></span></a>
    <span class="python.parameter.area">
     <span class="signature"><xsl:apply-templates select="$element/f:parameter"/></span>
    </span>
   </div>
   <xsl:apply-templates select="f:doc"/>
  </div>
 </xsl:template>

 <xsl:template name="parameter">
  <xsl:param name="element"/>
  <span id="{concat(../@xml:id, '..Parameters.', @identifier)}">
   <xsl:choose>
    <!-- keywords and variable do not have defaults -->
    <xsl:when test="$element/@type = 'keywords'">
     <xsl:attribute name="class"><xsl:text>keywords</xsl:text></xsl:attribute>
     <xsl:text>**</xsl:text>
    </xsl:when>

    <xsl:when test="$element/@type = 'variable'">
     <xsl:attribute name="class"><xsl:text>variable</xsl:text></xsl:attribute>
     <xsl:text>*</xsl:text>
    </xsl:when>

    <xsl:when test="$element/f:default">
     <xsl:attribute name="class"><xsl:text>optional</xsl:text></xsl:attribute>
    </xsl:when>

    <xsl:otherwise>
     <xsl:attribute name="class"><xsl:text>required</xsl:text></xsl:attribute>
    </xsl:otherwise>
   </xsl:choose>
   <span class="identifier"><xsl:value-of select="$element/@identifier"/></span>
  </span>
 </xsl:template>

 <xsl:template match="f:parameter[not(f:annotation) and f:default]">
  <!-- parameter with default, but no annotation -->
 </xsl:template>

 <xsl:template match="f:parameter[f:annotation or not(f:default)]">
  <a href="{df:reference(f:annotation/f:*)}">
   <xsl:attribute name="title">
    <xsl:value-of select="df:qname(f:annotation/f:*)"/>
   </xsl:attribute>
   <xsl:call-template name="parameter">
    <xsl:with-param name="element" select="."/>
   </xsl:call-template>
  </a><xsl:copy-of select="$arg.sep"/>
 </xsl:template>

 <xsl:template mode="python.bases" match="f:reference">
  <xsl:apply-templates mode="python.inline.data" select="."/>
  <span class="sequence-delimiter">,</span>
 </xsl:template>

 <xsl:template match="f:bases">
  <span class="python.bases">
   <xsl:apply-templates mode="python.bases" select="f:reference"/>
  </span>
 </xsl:template>

 <xsl:template match="f:data">
  <xsl:variable name="context" select="ancestor::f:*[@identifier][1]"/>
  <xsl:variable name="leading.name" select="$context/@identifier"/>
  <xsl:variable name="typ.addr" select="string(f:object/@type)"/>

  <div id="{ctx:id(.)}" class="data">
   <div class="title">
    <a href="#{ctx:id($context)}">
     <span class="identity-context"><xsl:value-of select="$leading.name"/>.</span>
    </a>
    <a href="#{@identifier}">
     <span class="identifier"><xsl:value-of select="@identifier"/></span>
    </a>
    <xsl:if test="$typ.addr">
     ::
     <a href="{ctx:absolute($typ.addr)}">
      <span class="identifier"><xsl:value-of select="ctx:typname($typ.addr)"/></span>
     </a>
    </xsl:if>
   </div>

   <xsl:choose>
    <xsl:when test="f:error">
     <div class="error">
      <xsl:apply-templates select="f:error"/>
     </div>
    </xsl:when>
    <xsl:otherwise>
     <div class="representation">
      <xsl:apply-templates mode="python.inline.data" select="./f:*"/>
     </div>
    </xsl:otherwise>
   </xsl:choose>
  </div>
 </xsl:template>

 <xsl:template match="f:import">
  <xsl:variable name="abs" select="ctx:absolute(string(@name))"/>
  <div class="import">
   <a class="import">
    <xsl:attribute name="href">
     <xsl:choose>
      <xsl:when test="$abs = ''">
       <xsl:value-of select="concat('https://docs.python.org/3/library/', @identifier, '.html')"/>
      </xsl:when>
      <xsl:otherwise>
       <xsl:value-of select="$abs"/>
      </xsl:otherwise>
     </xsl:choose>
    </xsl:attribute>
    <span class="identifier"><xsl:value-of select="@name"/></span>
   </a>
  </div>
 </xsl:template>

 <xsl:template match="f:property">
  <xsl:variable name="name" select="@identifier"/>
  <xsl:variable name="path" select="@xml:id"/>
  <xsl:variable name="leading.name" select="ancestor::f:*[@identifier][1]/@identifier"/>

  <div class="{local-name()}">
   <xsl:attribute name="id"><xsl:value-of select="@xml:id"/></xsl:attribute>
   <div class="title">
    <xsl:if test="(..)[local-name()='class']">
     <span class="identity-context"><xsl:value-of select="$leading.name"/></span>
     <span class="path-delimiter">.</span>
    </xsl:if>
    <a href="{concat('#', @xml:id)}"><span class="identifier"><xsl:value-of select="$name"/></span></a>
   </div>
   <xsl:apply-templates select="./f:doc"/>
  </div>
 </xsl:template>

 <xsl:template match="f:function">
  <xsl:variable name="name" select="@identifier"/>
  <xsl:variable name="path" select="@xml:id"/>
  <xsl:variable name="context" select="ancestor::f:*[@identifier][1]"/>
  <xsl:variable name="leading.name" select="$context/@identifier"/>

  <div class="function">
   <xsl:attribute name="id"><xsl:value-of select="@xml:id"/></xsl:attribute>
   <div class="title">
    <a href="#{ctx:id($context)}">
     <span class="identity-context"><xsl:value-of select="$leading.name"/></span>
    </a>
    <span class="path-delimiter">.</span>
    <a href="{concat('#',@xml:id)}"><span class="identifier"><xsl:value-of select="$name"/></span></a>
    <span class="python.parameter.area">
     <span class="signature"><xsl:apply-templates select="f:parameter"/></span>
    </span>
   </div>
   <xsl:apply-templates select="./f:doc"/>
  </div>
 </xsl:template>

 <xsl:template match="f:method">
  <xsl:call-template name="method">
   <xsl:with-param name="element" select="."/>
  </xsl:call-template>
 </xsl:template>

 <!-- Properties section inside class documentation -->
 <xsl:template mode="properties" match="e:section">
  <xsl:variable name="context" select="ancestor::f:*[@xml:id][1]"/>
  <xsl:variable name="leading.identifier" select="$context/@identifier"/>
  <xsl:variable name="prefix" select="$context/@xml:id"/>

  <xsl:for-each select="e:dictionary/e:item">
   <xsl:variable name="name" select="e:key//text()"/>
   <xsl:variable name="id" select="concat($prefix, '.', $name)"/>

   <div id="{$id}" class="property">
    <div class="title">
     <a href="#{ctx:id($context)}">
      <span class="identity-context">
       <xsl:value-of select="$leading.identifier"/>
      </span>
     </a>
     <span class="path-delimiter">.</span>
     <a href="{concat('#', $id)}">
      <span class="identifier"><xsl:value-of select="$name"/></span>
     </a>
    </div>
    <xsl:apply-templates select="e:value/e:*"/>
   </div>
  </xsl:for-each>
 </xsl:template>

 <xsl:template name="class">
  <xsl:param name="element"/>
  <xsl:variable name="properties.section" select="$element/f:doc/e:section[@identifier='Properties']"/>
  <xsl:variable name="has.properties" select="$element/f:property[f:doc] | $properties.section"/>

  <xsl:if test="$element/f:method[@type='class']">
   <div class="class_methods">
    <div class="head">
     <span class="title"><xsl:value-of select="$class_methods_title"/></span>
    </div>
    <xsl:apply-templates select="$element/f:method[@type='class']">
     <xsl:sort order="ascending" select="number($element/f:source/@start)"/>
    </xsl:apply-templates>
   </div>
  </xsl:if>

  <xsl:if test="$has.properties">
   <div class="properties">
    <div class="head">
     <span class="title"><xsl:value-of select="$properties_title"/></span>
    </div>
    <xsl:apply-templates select="$element/f:property"/>
    <xsl:apply-templates mode="properties" select="$element/f:doc/e:section[@identifier='Properties']"/>
   </div>
  </xsl:if>

  <xsl:if test="$element/f:method[not(@type)]">
   <!-- must be a plain method and have documentation -->
   <div class="methods">
    <div class="head">
     <span class="title"><xsl:value-of select="$methods_title"/></span>
    </div>
    <xsl:apply-templates select="$element/f:method[not(@type)]">
     <xsl:sort order="ascending" select="number($element/f:source/@start)"/>
    </xsl:apply-templates>
   </div>
  </xsl:if>

  <xsl:if test="$element/f:method[@type='static']">
   <div class="static_methods">
    <div class="head">
     <span class="title"><xsl:value-of select="$static_methods_title"/></span>
    </div>
    <xsl:apply-templates select="$element/f:method[@type='static']">
     <xsl:sort order="ascending" select="number($element/f:source/@start)"/>
    </xsl:apply-templates>
   </div>
  </xsl:if>

  <xsl:if test="$element/f:data">
   <div class="datas">
    <div class="head">
     <span class="title"><xsl:value-of select="$class_data_title"/></span>
    </div>
    <xsl:apply-templates select="$element/f:data"/>
   </div>
  </xsl:if>
 </xsl:template>

 <xsl:template match="f:class">
  <xsl:variable name="name" select="@identifier"/>
  <xsl:variable name="xmlid" select="@xml:id"/>

  <xsl:variable name="context" select="ancestor::f:*[@identifier][1]"/>
  <xsl:variable name="leading.name" select="$context/@identifier"/>

  <xsl:variable name="abstract.src" select="ctx:qualify(f:inherit.docs(.))"/>
  <xsl:apply-templates select="./f:class"/>

  <div id="{@xml:id}" class="class">
   <div class="title">
    <a href="#{ctx:id($context)}">
     <span class="identity-context"><xsl:value-of select="$leading.name"/></span>
    </a>
    <span class="path-delimiter">.</span>
    <a href="{concat('#', $xmlid)}"><span class="identifier"><xsl:value-of select="$name"/></span></a>
    <span class="python.parameter.area">
     <span class="parameters.open">(</span>
      <xsl:apply-templates select="f:bases"/>
     <span class="parameters.close">)</span>
    </span>
   </div>

   <div class="doc">
    <xsl:apply-templates select="f:doc/e:*[not(@identifier='Properties')]"/>
   </div>

   <div class="content">
    <xsl:if test="false and $abstract.src != ''">
     <xsl:variable name="docclass" select="ctx:site.element($abstract.src)"/>
     <xsl:variable name="prefix" select="$docclass/@identifier"/>

     <xsl:variable name="se">
      <f:factor identifier="{/f:factor/@identifier}">
       <xsl:copy-of select="ancestor::f:factor/f:context"/>

       <f:module identifier="{/f:factor/@identifier}">
        <f:class identifier="{$name}">
         <xsl:attribute name="id" namespace="http://www.w3.org/XML/1998/namespace" select="$xmlid"/>
         <xsl:for-each select="$docclass/f:*">
          <xsl:element name="{local-name()}" namespace="namespace-uri()">
           <xsl:if test="@xml:id">
            <xsl:attribute name="id" namespace="http://www.w3.org/XML/1998/namespace"
             select="concat($xmlid, substring-after(@xml:id, $prefix))"/>
           </xsl:if>
           <xsl:message><xsl:value-of select="concat($prefix, ' g ', local-name(), '  ', concat($xmlid, substring-after(@xml:id, $prefix)))"/></xsl:message>

           <xsl:copy-of select="@*[local-name()!='xml:id']"/>
           <xsl:copy-of select="./*|./text()"/>
          </xsl:element>
         </xsl:for-each>
        </f:class>
       </f:module>
      </f:factor>
     </xsl:variable>
     <xsl:message><xsl:value-of select="exsl:node-set($se)/f:factor/f:module/f:class/@xml:id"/></xsl:message>
     <xsl:call-template name="class">
      <xsl:with-param name="element" select="exsl:node-set($se)/f:factor/f:module/f:class"/>
     </xsl:call-template>
    </xsl:if>

    <xsl:call-template name="class">
     <xsl:with-param name="element" select="."/>
    </xsl:call-template>
   </div>
  </div>
 </xsl:template>

 <xsl:template match="f:module">
  <xsl:variable name="name" select="@identifier"/>
  <xsl:variable name="path" select="@name"/>
  <xsl:variable name="parent" select="substring-before(@name, concat('.', $name))"/>

  <xsl:apply-templates select="./f:doc/e:section[not(@identifier) or @identifier!='Properties']"/>
  <xsl:apply-templates select="./f:error"/>

  <div class="content">
   <xsl:if test="./f:data">
    <div class="datas">
     <div class="head">
      <span class="title"><xsl:value-of select="$data_title"/></span>
     </div>
     <xsl:apply-templates select="./f:data"/>
    </div>
   </xsl:if>

   <xsl:if test="./f:function">
    <div class="functions">
     <div class="head">
      <span class="title"><xsl:value-of select="$functions_title"/></span>
     </div>

     <xsl:apply-templates select="./f:function[f:doc]">
      <xsl:sort order="ascending" select="number(./f:source/@start)"/>
     </xsl:apply-templates>

     <div class="undocumented">
      <xsl:apply-templates select="./f:function[not(f:doc)]">
       <xsl:sort order="ascending" select="number(./f:source/@start)"/>
      </xsl:apply-templates>
     </div>
    </div>
   </xsl:if>

   <xsl:if test="./f:class">
    <div class="classes">
     <div class="head">
      <span class="title"><xsl:value-of select="$classes_title"/></span>
     </div>

     <xsl:apply-templates select="./f:class[f:doc]">
      <xsl:sort order="ascending" select="number(./f:source/@start)"/>
     </xsl:apply-templates>

     <div class="undocumented">
      <xsl:apply-templates select="./f:class[not(f:doc)]">
       <xsl:sort order="ascending" select="number(./f:source/@start)"/>
      </xsl:apply-templates>
     </div>
    </div>
   </xsl:if>
  </div>
 </xsl:template>

 <xsl:template match="f:subfactor">
  <!-- units that are contained by the factor, but distinct -->
  <xsl:variable name="name" select="concat(../f:module/@name, '.', @identifier)"/>
  <xsl:variable name="icon" select="ctx:icon($name)"/>

  <a href="{concat($name, $reference_suffix)}">
   <div class="subfactor">
    <xsl:choose>
     <xsl:when test="$icon">
      <div class="icon"><xsl:value-of select="$icon"/></div>
     </xsl:when>
     <xsl:otherwise>
      <div class="icon"><img class="icon" src="python.svg"/></div>
     </xsl:otherwise>
    </xsl:choose>
    <div class="label">
     <span class="identifier"><xsl:value-of select="@identifier"/></span>
    </div>
    <div class="abstract"><xsl:copy-of select="ctx:abstract($name)"/></div>
   </div>
  </a>
 </xsl:template>
</xsl:transform>
<!--
 ! vim: et:sw=1:ts=1
 !-->
