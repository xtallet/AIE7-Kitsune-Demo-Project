-- FUNCTION: demo.get_last_endorsement_id(text)

-- DROP FUNCTION IF EXISTS demo.get_last_endorsement_id(text);

CREATE OR REPLACE FUNCTION demo.get_last_endorsement_id(
	p_reference character varying)
    RETURNS TABLE(id uuid)
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE PARALLEL UNSAFE
    ROWS 1000

AS $BODY$
BEGIN
    RETURN QUERY
    SELECT pm.id
    FROM demo.policies_policymodel pm
    INNER JOIN demo.policies_policymodel t2
        ON pm.original_policy_without_endorsement_id = t2.id
    CROSS JOIN (SELECT p_reference AS reference) mv
    WHERE pm.is_endorsement IS TRUE
        AND pm.reference = mv.reference
        AND pm.status = (
            CASE
                WHEN (
                    pm.internal_expiry_date >= (
                        SELECT U0.internal_expiry_date
                        FROM demo.policies_policymodel U0
                        CROSS JOIN (SELECT p_reference AS reference) mv_sub
                        WHERE U0.reference = mv_sub.reference
                        LIMIT 1
                    )
                    AND t2.status = 'expired'
                    AND pm.status = 'expired'
                )
                    THEN 'expired'
                WHEN pm.status = 'cancelled'
                    THEN 'cancelled'
                WHEN (
                    pm.effective_date <= CURRENT_DATE
                    AND pm.internal_expiry_date >= CURRENT_DATE
                    AND t2.status = 'bound'
                    AND pm.status = 'bound'
                )
                    THEN 'bound'
                ELSE 'draft'
            END
        )
    ORDER BY pm.version DESC
	LIMIT 1;
END;
$BODY$;

ALTER FUNCTION demo.get_last_endorsement_id(character varying)
    OWNER TO data_app;
