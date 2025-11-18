<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="2.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <!-- Main template: PowerUsageData to EmissionReport -->
  <xsl:template match="PowerUsageData">
    <EmissionReport>
      <xsl:apply-templates select="Facility"/>
    </EmissionReport>
  </xsl:template>

  <!--
    Facility template: Calculate CO2 emission
    Formula: totalEmission = PowerConsumption × EmissionFactor

    Constraints checked:
    - PowerConsumption >= 0 (from source XSD)
    - EmissionFactor > 0 (from source XSD)
    - Year >= 2020 (business rule: only recent data)
  -->
  <xsl:template match="Facility">
    <xsl:if test="PowerConsumption &gt;= 0 and EmissionFactor &gt; 0 and Year &gt;= 2020">
      <FacilityEmission>
        <xsl:attribute name="facility">
          <xsl:value-of select="FacilityName"/>
        </xsl:attribute>

        <!-- CALCULATION: CO2 emission = power × emission factor -->
        <xsl:attribute name="totalEmission">
          <xsl:value-of select="PowerConsumption * EmissionFactor"/>
        </xsl:attribute>

        <xsl:attribute name="year">
          <xsl:value-of select="Year"/>
        </xsl:attribute>

        <!-- Verified flag: true if emission factor is from official source (> 0.3) -->
        <xsl:attribute name="verified">
          <xsl:choose>
            <xsl:when test="EmissionFactor &gt;= 0.3">true</xsl:when>
            <xsl:otherwise>false</xsl:otherwise>
          </xsl:choose>
        </xsl:attribute>
      </FacilityEmission>
    </xsl:if>
  </xsl:template>

</xsl:stylesheet>
