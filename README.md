# AMI
Asset Management &amp; Intelligence

PREFIX ex: <http://example.org/schema#>
SELECT ?software
WHERE {
  ?software ex:dependencies+ ex:software1 .
}

