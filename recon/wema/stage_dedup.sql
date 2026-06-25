WITH base AS (
    SELECT *,
           MD5(
               transaction_id || COALESCE(transaction_reference, '') || amount::text || transaction_type
           ) AS hash_id
    FROM {{ params.schema }}.{{ params.raw}}
    WHERE ingestion_date >= CURRENT_DATE - INTERVAL '{{ params.lookback_days }} day'
),
dedup AS (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY hash_id
               ORDER BY created_at DESC
           ) AS rn
    FROM base
)
INSERT INTO {{ params.schema }}.{{ params.staging}} (
    transaction_id,
    account_id,
    amount,
    transaction_type,
    transaction_reference,
    narration,
    created_at,
    ingestion_date,
    hash_id
)
SELECT
    transaction_id,
    account_id,
    amount,
    transaction_type,
    transaction_reference,
    narration,
    created_at,
    ingestion_date,
    hash_id
FROM dedup
WHERE rn = 1
ON CONFLICT (transaction_id) DO UPDATE SET
    account_id = EXCLUDED.account_id,
    amount = EXCLUDED.amount,
    transaction_type = EXCLUDED.transaction_type,
    transaction_reference = EXCLUDED.transaction_reference,
    narration = EXCLUDED.narration,
    created_at = EXCLUDED.created_at,
    ingestion_date = EXCLUDED.ingestion_date,
    hash_id = EXCLUDED.hash_id;