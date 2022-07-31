Get list of all domains and their whois info
Relays per domain per country

Get list of Infra providers
Relays per Datacenter (AWS, DigitalOcean .....)
----
SELECT country, org, SUM(total_proofs) as relays
FROM public.transaction
WHERE msg_type = 'claim' and NOT(org is NULL) and (org != '') and (result_code = 0)
GROUP BY country, org
ORDER BY relays DESC
----
Relays per Country




---
Relays per domain
SELECT sum(total_proofs) as tp, SUBSTRING(servicer_url, POSITION('.' IN servicer_url)+1,100) AS servicer_domain
FROM public.transaction
WHERE msg_type = 'claim' and NOT(org is NULL) and (org != '') and (result_code = 0)
GROUP BY servicer_domain
ORDER BY tp DESC
---
--SELECT sum(total_proofs) as tp, SUBSTRING(servicer_url, POSITION('.' IN servicer_url)+1,100) AS servicer_domain


SELECT sum(total_proofs) as tp, (REGEXP_MATCHES(servicer_url, 
         '([a-z0-9_\-]+\.[a-z0-9_\-]+$)'))[1] AS servicer_domain
FROM public.transaction
WHERE msg_type = 'claim' and NOT(org is NULL) and (org != '') and (result_code = 0)
GROUP BY servicer_domain
ORDER BY tp DESC

