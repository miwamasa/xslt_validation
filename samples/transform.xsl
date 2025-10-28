<?xml version="1.0" encoding="UTF-8"?>
<!-- transform.xsl -->
<xsl:stylesheet version="2.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:template match="Person">
    <xsl:if test="Age >= 0">
      <Individual fullname="{Name}" years="{Age}"/>
    </xsl:if>
  </xsl:template>
</xsl:stylesheet>
