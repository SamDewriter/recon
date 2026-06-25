CREATE TABLE IF NOT EXISTS {{ params.schema }}.{{ params.raw}} (
    transaction_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    amount NUMERIC(18, 2) NOT NULL,
    transaction_type TEXT NOT NULL,
    transaction_reference TEXT,
    narration TEXT,
    created_at TIMESTAMP NOT NULL,
    ingestion_date TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS {{ params.schema }}.{{ params.staging}} (
    transaction_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    amount NUMERIC(18, 2) NOT NULL,
    transaction_type TEXT NOT NULL,
    transaction_reference TEXT,
    narration TEXT,
    created_at TIMESTAMP NOT NULL,
    ingestion_date TIMESTAMP NOT NULL,
    hash_id TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS {{ params.schema }}.{{ params.recon_results}} (
    transaction_reference TEXT,
    credit_transaction_id TEXT,
    debit_transaction_id TEXT,
    credit_amount NUMERIC(18, 2),
    debit_amount NUMERIC(18, 2),
    reconciliation_status TEXT NOT NULL,
    run_date TIMESTAMP NOT NULL
);