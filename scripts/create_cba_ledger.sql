CREATE TABLE ledger_transactions (
    transaction_id      VARCHAR(50) PRIMARY KEY,
    account_id          VARCHAR(50) NOT NULL,
    account_number      VARCHAR(10) NOT NULL,
    transaction_reference     VARCHAR(80) NOT NULL,
    transaction_type    VARCHAR(10) NOT NULL
        CHECK (transaction_type IN ('CREDIT', 'DEBIT')),
    amount              NUMERIC(18, 2) NOT NULL
        CHECK (amount > 0),
    currency            VARCHAR(3) NOT NULL DEFAULT 'NGN',
    narration           TEXT,
    status              VARCHAR(20) NOT NULL
        CHECK (status IN ('SUCCESS', 'FAILED', 'PENDING', 'REVERSED')),
    channel             VARCHAR(30),
    value_date          DATE NOT NULL,
    created_at          TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP,
    initiated_by        VARCHAR(50),
    approval_status     VARCHAR(20)
);
