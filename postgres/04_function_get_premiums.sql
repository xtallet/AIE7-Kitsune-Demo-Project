-- FUNCTION: demo.get_premiums()

-- DROP FUNCTION IF EXISTS demo.get_premiums();

CREATE OR REPLACE FUNCTION demo.get_premiums(
	)
    RETURNS TABLE(policy_id uuid, policy_reference character varying, is_endorsement boolean, status_group character varying, premium numeric)
    LANGUAGE 'sql'
    COST 100
    VOLATILE PARALLEL UNSAFE
    ROWS 1000

AS $BODY$

WITH endorsements_count AS (
    SELECT
        reference AS policy_reference,
        COUNT(id) AS num_of_end
    FROM demo.policies_policymodel
	WHERE status != 'draft'
    GROUP BY reference
    ORDER BY reference ASC
),
if_endorsements AS (
    SELECT
        policy_reference
		,CASE
			WHEN (SELECT demo.get_last_endorsement_id(policy_reference) LIMIT 1) is null
			THEN (SELECT id FROM demo.policies_policymodel WHERE reference = policy_reference and version = 0)
			ELSE (SELECT demo.get_last_endorsement_id(policy_reference))
		END AS last_endorsement_id
    FROM endorsements_count
    WHERE num_of_end > 1
),
endorsement_premiums AS (
    SELECT
		(SELECT id FROM demo.policies_policymodel WHERE reference = policy_reference AND id = last_endorsement_id) AS policy_id
        ,policy_reference
        ,demo.total_gross_premium(last_endorsement_id) AS premium
        ,(SELECT status FROM demo.policies_policymodel WHERE reference = policy_reference AND id = last_endorsement_id) AS status
		,true as "is_endorsement"
    FROM if_endorsements
    --ORDER BY premium DESC NULLS LAST
),
policy_premiums AS (
    SELECT
		(SELECT id FROM demo.policies_policymodel WHERE reference = policy_reference AND version = 0) AS policy_id
        ,policy_reference
        ,demo.total_gross_premium((SELECT id FROM demo.policies_policymodel WHERE reference = policy_reference AND version = 0)) AS premium
        ,(SELECT status FROM demo.policies_policymodel WHERE reference = policy_reference AND version = 0) AS status
		,false as "is_endorsement"
    FROM endorsements_count
    WHERE num_of_end = 1
    --ORDER BY premium DESC NULLS LAST
),
combined_premiums AS (
    SELECT
		policy_id
        ,policy_reference
        ,CASE
            WHEN status IN ('bound', 'expired', 'endorsement-cancelled') THEN 'written'
            WHEN status NOT IN ('bound', 'expired', 'endorsement-cancelled') THEN 'not_written'
        END AS status_group
        ,premium
		,is_endorsement
    FROM endorsement_premiums
    UNION ALL
    SELECT
		policy_id
        ,policy_reference
        ,CASE
            WHEN status IN ('bound', 'expired', 'endorsement-cancelled') THEN 'written'
            WHEN status NOT IN ('bound', 'expired', 'endorsement-cancelled') THEN 'not_written'
        END AS status_group
        ,premium
		,is_endorsement
    FROM policy_premiums
)
SELECT policy_id, policy_reference, is_endorsement, status_group, premium
FROM combined_premiums;
$BODY$;

ALTER FUNCTION demo.get_premiums()
    OWNER TO data_app;
