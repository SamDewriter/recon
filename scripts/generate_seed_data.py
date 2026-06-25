#!/usr/bin/env python3
"""
Generates realistic seed data for cba_ledger_transactions.

Usage:
    python generate_seed_data.py                     # writes seed_data.csv next to this script
    python generate_seed_data.py output.csv          # writes to a custom path

Scenarios generated per day:
    - Matched pairs      : DEBIT + CREDIT with equal amounts (happy path)
    - Orphan debits      : DEBIT with no corresponding CREDIT (missing_credit)
    - Amount mismatches  : DEBIT + CREDIT where amounts differ (fee deducted)
    - Reversed pairs     : DEBIT reversed after initial SUCCESS
"""

import csv
import random
import sys
import uuid
from datetime import datetime, timedelta, date
from decimal import Decimal
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BANK_CODES = {
    "wema":      "000022111",
    "gtb":       "000022112",
    "firstbank": "000022113",
}

# Each bank has a single fixed settlement account number
SETTLEMENT_ACCOUNTS = {
    "wema":      "0000221110",
    "gtb":       "0000221120",
    "firstbank": "0000221130",
}

CHANNELS        = ["BANK_TRANSFER", "USSD", "CARD", "WALLET"]
CHANNEL_WEIGHTS = [0.55,            0.20,   0.15,   0.10]

NIGERIAN_NAMES = [
    "Chukwuemeka Obi",   "Amaka Nwosu",       "Babatunde Adeyemi",
    "Ngozi Eze",         "Emeka Okafor",       "Fatima Aliyu",
    "Kelechi Onyekachi", "Adaeze Nwachukwu",  "Olumide Adewale",
    "Chioma Okonkwo",    "Ibrahim Musa",       "Yetunde Akinsanya",
    "Chidi Obiora",      "Aisha Mohammed",     "Tunde Fashola",
    "Nneka Chukwu",      "Umar Faruk",         "Blessing Okafor",
    "Seun Afolabi",      "Chinwe Agu",
]

NARRATION_TEMPLATES = [
    "Transfer to {name}",
    "Payment from {name}",
    "Salary payment {month}",
    "School fees - {month}",
    "Rent payment {month}",
    "Business payment to {name}",
    "NIP/TRSF/{ref}",
    "Mobile banking transfer to {name}",
    "Online payment ref {ref}",
    "Settlement {ref}",
    "Utility bill payment",
    "POS purchase at {merchant}",
]

MERCHANTS = [
    "SHOPRITE NG", "GAME STORES", "JUSTRITE SUPERSTORE",
    "NEXT SUPERMARKET", "CHICKEN REPUBLIC", "DOMINOS PIZZA",
]

COLUMNS = [
    "transaction_id", "account_id", "account_number", "transaction_reference",
    "transaction_type", "amount", "currency", "narration",
    "status", "channel", "value_date", "created_at", "updated_at",
    "initiated_by", "approval_status",
]

DAYS_OF_DATA = 90

# Weekday volumes (Mon–Fri)
WEEKDAY = dict(matched=75, orphan=7, mismatch=4, reversal=3)
# Weekend volumes (Sat–Sun) — lower but non-zero
WEEKEND = dict(matched=35, orphan=3, mismatch=2, reversal=1)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def gen_account_id(bank: str, account_number: str) -> str:
    return f"ACC-{bank.upper()}-{account_number}"

def gen_transaction_id(ts: datetime) -> str:
    return f"TXN{ts.strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6].upper()}"

def gen_transaction_reference(ts: datetime) -> str:
    return f"NIP{ts.strftime('%Y%m%d%H%M%S')}{random.randint(100000, 999999)}"

def gen_amount() -> Decimal:
    band = random.choices(
        [100, 500, 1_000, 5_000, 50_000, 200_000],
        weights=[5, 10, 40, 30, 10, 5],
    )[0]
    multiplier = random.randint(1, 20)
    return Decimal(str(band * multiplier))

def gen_narration(recon_ref: str) -> str:
    tpl = random.choice(NARRATION_TEMPLATES)
    return tpl.format(
        name=random.choice(NIGERIAN_NAMES),
        month=datetime.now().strftime("%B %Y"),
        ref=recon_ref[-8:],
        merchant=random.choice(MERCHANTS),
    )

def rand_ts(base: date, hour_range=(8, 22)) -> datetime:
    return datetime(
        base.year, base.month, base.day,
        random.randint(*hour_range),
        random.randint(0, 59),
        random.randint(0, 59),
    )

def rand_channel() -> str:
    return random.choices(CHANNELS, CHANNEL_WEIGHTS)[0]

def rand_bank() -> str:
    return random.choice(list(BANK_CODES.keys()))

# ---------------------------------------------------------------------------
# Row builders
# ---------------------------------------------------------------------------

def make_row(
    ts: datetime,
    account_number: str,
    bank: str,
    recon_ref: str,
    txn_type: str,
    amount: Decimal,
    narration: str,
    channel: str,
    status: str = "SUCCESS",
    initiated_by: str | None = None,
    approval_status: str = "APPROVED",
    updated_at: datetime | None = None,
) -> dict:
    return {
        "transaction_id":   gen_transaction_id(ts),
        "account_id":       gen_account_id(bank, account_number),
        "account_number":   account_number,
        "transaction_reference":  recon_ref,
        "transaction_type": txn_type,
        "amount":           amount,
        "currency":         "NGN",
        "narration":        narration,
        "status":           status,
        "channel":          channel,
        "value_date":       ts.date(),
        "created_at":       ts,
        "updated_at":       updated_at or ts + timedelta(seconds=2),
        "initiated_by":     initiated_by or f"user_{random.randint(1000, 9999)}",
        "approval_status":  approval_status,
    }


def gen_matched_pair(base: date) -> list[dict]:
    """DEBIT + CREDIT with the same amount — reconciles as 'matched'."""
    debit_bank, credit_bank = random.sample(list(SETTLEMENT_ACCOUNTS), 2)
    ts_debit  = rand_ts(base)
    ts_credit = ts_debit + timedelta(seconds=random.randint(1, 30))
    recon_ref = gen_transaction_reference(ts_debit)
    amount    = gen_amount()
    channel   = rand_channel()
    narration = gen_narration(recon_ref)
    initiator = f"user_{random.randint(1000, 9999)}"

    return [
        make_row(ts_debit,  SETTLEMENT_ACCOUNTS[debit_bank],  debit_bank,  recon_ref, "DEBIT",  amount, narration, channel, initiated_by=initiator),
        make_row(ts_credit, SETTLEMENT_ACCOUNTS[credit_bank], credit_bank, recon_ref, "CREDIT", amount, narration, channel, initiated_by=initiator),
    ]


def gen_orphan_debit(base: date) -> list[dict]:
    """DEBIT with no corresponding CREDIT — reconciles as 'missing_credit'."""
    bank      = rand_bank()
    ts        = rand_ts(base)
    recon_ref = gen_transaction_reference(ts)
    return [
        make_row(
            ts, SETTLEMENT_ACCOUNTS[bank], bank, recon_ref,
            "DEBIT", gen_amount(), gen_narration(recon_ref), rand_channel(),
            status="PENDING", approval_status="PENDING", updated_at=None,
        )
    ]


def gen_amount_mismatch(base: date) -> list[dict]:
    """DEBIT + CREDIT where credit amount is lower — reconciles as 'amount_mismatch'."""
    debit_bank, credit_bank = random.sample(list(SETTLEMENT_ACCOUNTS), 2)
    ts_debit  = rand_ts(base)
    ts_credit = ts_debit + timedelta(seconds=random.randint(1, 30))
    recon_ref = gen_transaction_reference(ts_debit)
    debit_amount  = gen_amount()
    fee           = Decimal(str(random.choice([50, 100, 200, 500])))
    fee           = min(fee, debit_amount - Decimal("1.00"))
    credit_amount = debit_amount - fee
    channel       = rand_channel()
    narration     = gen_narration(recon_ref)
    initiator     = f"user_{random.randint(1000, 9999)}"

    return [
        make_row(ts_debit,  SETTLEMENT_ACCOUNTS[debit_bank],  debit_bank,  recon_ref, "DEBIT",  debit_amount,  narration, channel, initiated_by=initiator),
        make_row(ts_credit, SETTLEMENT_ACCOUNTS[credit_bank], credit_bank, recon_ref, "CREDIT", credit_amount, narration, channel, initiated_by=initiator),
    ]


def gen_reversal(base: date) -> list[dict]:
    """SUCCESS DEBIT followed by a REVERSED entry on the same reference."""
    bank        = rand_bank()
    ts_debit    = rand_ts(base)
    ts_reversal = ts_debit + timedelta(minutes=random.randint(5, 60))
    recon_ref   = gen_transaction_reference(ts_debit)
    amount      = gen_amount()
    channel     = rand_channel()
    narration   = gen_narration(recon_ref)
    initiator   = f"user_{random.randint(1000, 9999)}"
    acct        = SETTLEMENT_ACCOUNTS[bank]

    return [
        make_row(ts_debit,    acct, bank, recon_ref, "DEBIT", amount, narration, channel, status="SUCCESS",  initiated_by=initiator),
        make_row(ts_reversal, acct, bank, recon_ref, "DEBIT", amount, narration, channel, status="REVERSED", initiated_by=initiator),
    ]


# ---------------------------------------------------------------------------
# CSV serialisation
# ---------------------------------------------------------------------------

def _csv_val(v) -> str:
    if v is None:
        return ""
    if isinstance(v, Decimal):
        return str(v)
    if isinstance(v, datetime):
        return v.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(v, date):
        return v.strftime("%Y-%m-%d")
    return str(v)


def write_csv(rows: list[dict], out_path: Path) -> None:
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(COLUMNS)
        for row in rows:
            writer.writerow([_csv_val(row[c]) for c in COLUMNS])


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    out_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "seed_data.csv"

    random.seed(42)
    today = date.today()
    rows: list[dict] = []

    for day_offset in range(DAYS_OF_DATA - 1, -1, -1):   # oldest → newest
        base   = today - timedelta(days=day_offset)
        volume = WEEKEND if base.weekday() >= 5 else WEEKDAY

        for _ in range(volume["matched"]):
            rows.extend(gen_matched_pair(base))
        for _ in range(volume["orphan"]):
            rows.extend(gen_orphan_debit(base))
        for _ in range(volume["mismatch"]):
            rows.extend(gen_amount_mismatch(base))
        for _ in range(volume["reversal"]):
            rows.extend(gen_reversal(base))

    rows.sort(key=lambda r: r["created_at"])

    write_csv(rows, out_path)
    start_date = today - timedelta(days=DAYS_OF_DATA - 1)
    print(f"Wrote {len(rows)} rows ({start_date} → {today}) → {out_path}")


if __name__ == "__main__":
    main()
