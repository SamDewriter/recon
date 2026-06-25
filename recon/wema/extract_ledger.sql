INSERT INTO {{ params.schema }}.{{ params.raw}} (
    transaction_id,
    account_id,
    amount,
    transaction_type,
    transaction_reference,
    narration,
    created_at,
    ingestion_date
)
SELECT
    transaction_id,
    account_id,
    amount,
    transaction_type,
    transaction_reference,
    narration,
    created_at,
    '{{ ts }}'::timestamp
FROM {{ params.ledger_schema }}.ledger_transactions
WHERE account_number = '{{ params.account_number }}'
  AND created_at >= NOW() - INTERVAL '{{ params.lookback_days }} day';
