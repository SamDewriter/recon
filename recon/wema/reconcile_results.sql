INSERT INTO {{ params.schema }}.{{ params.recon_results}} (
    transaction_reference,
    credit_transaction_id,
    debit_transaction_id,
    credit_amount,
    debit_amount,
    reconciliation_status,
    run_date
)
SELECT
    transaction_reference,
    credit_transaction_id,
    debit_transaction_id,
    credit_amount,
    debit_amount,
    reconciliation_status,
    '{{ ts }}'::timestamp
FROM {{ params.schema }}.{{ params.reconciliation}};
