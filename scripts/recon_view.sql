CREATE OR REPLACE VIEW {{ params.schema }}.{{ params.reconciliation}} AS
WITH base AS (
    SELECT *
    FROM {{ params.schema }}.recon_staging_ledger
),
credit AS (
    SELECT *
    FROM base
    WHERE transaction_type = 'CREDIT'
),
debit AS (
    SELECT *
    FROM base
    WHERE transaction_type = 'DEBIT'
)
SELECT
    COALESCE(c.transaction_reference, d.transaction_reference) AS transaction_reference,
    c.transaction_id AS credit_transaction_id,
    d.transaction_id AS debit_transaction_id,
    c.amount AS credit_amount,
    d.amount AS debit_amount,
    CASE
        WHEN c.transaction_id IS NULL THEN 'missing_credit'
        WHEN d.transaction_id IS NULL THEN 'missing_debit'
        WHEN c.amount = d.amount THEN 'matched'
        ELSE 'amount_mismatch'
    END AS reconciliation_status
FROM credit c
FULL OUTER JOIN debit d
    ON c.transaction_reference = d.transaction_reference;

