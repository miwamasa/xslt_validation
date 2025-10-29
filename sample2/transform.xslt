<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="2.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <!-- Main template: Company to Organization -->
  <xsl:template match="Company">
    <Organization>
      <xsl:apply-templates select="Employee"/>
      <xsl:apply-templates select="Department"/>
    </Organization>
  </xsl:template>

  <!-- Employee to Staff: only non-interns, adults with positive salary -->
  <xsl:template match="Employee">
    <xsl:if test="Role != 'intern' and Age &gt;= 18 and Salary &gt; 0">
      <Staff fullName="{Name}" age="{Age}">
        <xsl:attribute name="position">
          <xsl:choose>
            <xsl:when test="Role = 'manager'">lead</xsl:when>
            <xsl:when test="Role = 'developer'">engineer</xsl:when>
            <xsl:otherwise>engineer</xsl:otherwise>
          </xsl:choose>
        </xsl:attribute>
        <xsl:attribute name="income">
          <xsl:value-of select="Salary"/>
        </xsl:attribute>
      </Staff>
    </xsl:if>
  </xsl:template>

  <!-- Department to Division: only with non-negative budget -->
  <xsl:template match="Department">
    <xsl:if test="Budget &gt;= 0">
      <Division title="{Name}" funds="{Budget}"/>
    </xsl:if>
  </xsl:template>

</xsl:stylesheet>
