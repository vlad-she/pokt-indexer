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
