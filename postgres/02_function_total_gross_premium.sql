-- FUNCTION: demo.total_gross_premium(uuid)

-- DROP FUNCTION IF EXISTS demo.total_gross_premium(uuid);

CREATE OR REPLACE FUNCTION demo.total_gross_premium(
	p_policy_id uuid)
    RETURNS numeric
    LANGUAGE 'sql'
    COST 100
    STABLE PARALLEL SAFE
AS $BODY$

SELECT (sum(p_lm.total_layer_premium))::numeric(25,7)
FROM demo.policies_limitmodel p_lm
WHERE p_lm.policy_id = p_policy_id

$BODY$;

ALTER FUNCTION demo.total_gross_premium(uuid)
    OWNER TO data_app;
