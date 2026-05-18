from __future__ import annotations

import csv
import json
import random
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

import duckdb
from faker import Faker

NULL_TOKEN = "\\N"
DEFAULT_SEED = 42
DEFAULT_USER_COUNT = 900
DEFAULT_MERCHANT_COUNT = 160
DEFAULT_LOGICAL_TX_COUNT = 6500

USER_FIELDS = [
    "user_id",
    "created_at",
    "country",
    "acquisition_channel",
    "kyc_status",
    "kyc_completed_at",
    "is_business",
]

ACCOUNT_FIELDS = [
    "account_id",
    "user_id",
    "account_type",
    "currency",
    "opened_at",
    "status",
]

MERCHANT_FIELDS = [
    "merchant_id",
    "merchant_name",
    "category",
    "merchant_country",
]

TRANSACTION_EVENT_FIELDS = [
    "event_id",
    "logical_tx_id",
    "processor_reference",
    "src_account_id",
    "dest_account_id",
    "merchant_id",
    "amount",
    "fee_amount",
    "currency",
    "tx_type",
    "event_status",
    "event_time",
    "ingested_at",
]


@dataclass(frozen=True)
class PracticePaths:
    root: Path
    practice_data_dir: Path
    artifacts_dir: Path
    duckdb_path: Path
    manifest_path: Path
    schema_path: Path


def resolve_paths(base_dir: Path | None = None) -> PracticePaths:
    package_root = Path(__file__).resolve().parents[1]
    root = Path(base_dir or package_root)
    practice_data_dir = root / "practice_data"
    artifacts_dir = root / "artifacts"
    return PracticePaths(
        root=root,
        practice_data_dir=practice_data_dir,
        artifacts_dir=artifacts_dir,
        duckdb_path=artifacts_dir / "screening_prep.duckdb",
        manifest_path=artifacts_dir / "dataset_manifest.json",
        schema_path=package_root / "sql" / "schema.sql",
    )


def _dt(value: datetime) -> str:
    return value.strftime("%Y-%m-%d %H:%M:%S")


def _fmt(value: object) -> str:
    if value is None:
        return NULL_TOKEN
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, datetime):
        return _dt(value)
    return str(value)


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: _fmt(row.get(field)) for field in fieldnames})


def _weighted_choice(rng: random.Random, items: list[tuple[str, float]]) -> str:
    labels = [label for label, _ in items]
    weights = [weight for _, weight in items]
    return rng.choices(labels, weights=weights, k=1)[0]


def _merchant_categories() -> list[str]:
    return [
        "grocery",
        "travel",
        "software",
        "marketplace",
        "restaurants",
        "healthcare",
        "logistics",
        "utilities",
        "education",
        "entertainment",
    ]


def _countries() -> list[str]:
    return ["US", "CA", "GB", "DE", "FR", "AU", "SG", "BR", "IN", "NL"]


def _generate_users(rng: random.Random, fake: Faker, user_count: int) -> list[dict[str, object]]:
    start = datetime(2024, 1, 1, 8, 0, 0)
    rows: list[dict[str, object]] = []
    for _ in range(user_count):
        created_at = start + timedelta(
            days=rng.randint(0, 460),
            hours=rng.randint(0, 23),
            minutes=rng.randint(0, 59),
        )
        kyc_status = _weighted_choice(
            rng,
            [("verified", 0.78), ("pending", 0.15), ("rejected", 0.07)],
        )
        kyc_completed_at = None
        if kyc_status == "verified":
            kyc_completed_at = created_at + timedelta(hours=rng.randint(2, 360))
        rows.append(
            {
                "user_id": uuid.uuid4(),
                "created_at": created_at,
                "country": _weighted_choice(
                    rng,
                    [
                        ("US", 0.34),
                        ("CA", 0.08),
                        ("GB", 0.11),
                        ("DE", 0.08),
                        ("FR", 0.07),
                        ("AU", 0.06),
                        ("SG", 0.05),
                        ("BR", 0.08),
                        ("IN", 0.09),
                        ("NL", 0.04),
                    ],
                ),
                "acquisition_channel": _weighted_choice(
                    rng,
                    [
                        ("organic", 0.28),
                        ("paid_search", 0.18),
                        ("referral", 0.2),
                        ("partner", 0.14),
                        ("sales", 0.08),
                        ("affiliate", 0.12),
                    ],
                ),
                "kyc_status": kyc_status,
                "kyc_completed_at": kyc_completed_at,
                "is_business": rng.random() < 0.12,
            }
        )
    return rows


def _generate_accounts(
    rng: random.Random,
    users: list[dict[str, object]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for user in users:
        user_created_at = datetime.strptime(str(user["created_at"]), "%Y-%m-%d %H:%M:%S")
        account_count = rng.choices([1, 2, 3], weights=[0.52, 0.33, 0.15], k=1)[0]
        for _ in range(account_count):
            rows.append(
                {
                    "account_id": uuid.uuid4(),
                    "user_id": user["user_id"],
                    "account_type": _weighted_choice(
                        rng,
                        [("checking", 0.42), ("wallet", 0.33), ("savings", 0.15), ("merchant", 0.10)],
                    ),
                    "currency": _weighted_choice(
                        rng,
                        [("USD", 0.76), ("EUR", 0.12), ("GBP", 0.08), ("SGD", 0.04)],
                    ),
                    "opened_at": user_created_at + timedelta(hours=rng.randint(0, 240)),
                    "status": _weighted_choice(
                        rng,
                        [("active", 0.9), ("frozen", 0.04), ("closed", 0.06)],
                    ),
                }
            )
    return rows


def _generate_merchants(
    rng: random.Random,
    fake: Faker,
    merchant_count: int,
) -> list[dict[str, object]]:
    categories = _merchant_categories()
    countries = _countries()
    rows: list[dict[str, object]] = []
    seen_names: set[str] = set()
    while len(rows) < merchant_count:
        name = fake.company()
        if name in seen_names:
            continue
        seen_names.add(name)
        rows.append(
            {
                "merchant_id": uuid.uuid4(),
                "merchant_name": name,
                "category": rng.choice(categories),
                "merchant_country": rng.choice(countries),
            }
        )
    return rows


def _amount_for_type(rng: random.Random, tx_type: str) -> float:
    if tx_type == "card_purchase":
        return round(rng.uniform(8, 340), 2)
    if tx_type == "transfer":
        return round(rng.uniform(25, 1800), 2)
    if tx_type == "cash_out":
        return round(rng.uniform(40, 900), 2)
    return round(rng.uniform(5, 220), 2)


def _fee_for(tx_type: str, amount: float, event_status: str) -> float:
    if event_status != "settled":
        return 0.0
    if tx_type == "card_purchase":
        return round(amount * 0.018, 2)
    if tx_type == "transfer":
        return round(amount * 0.004, 2)
    if tx_type == "cash_out":
        return round(amount * 0.012, 2)
    return round(amount * 0.006, 2)


def _event_sequence(rng: random.Random, tx_type: str) -> list[tuple[str, int]]:
    outcome = _weighted_choice(
        rng,
        [("settled", 0.82), ("declined", 0.13), ("reversed", 0.05)],
    )
    pending_offset = rng.randint(1, 6)
    settled_offset = pending_offset + rng.randint(2, 360)
    if outcome == "declined":
        return [("pending", pending_offset), ("declined", settled_offset)]
    if outcome == "reversed":
        return [
            ("pending", pending_offset),
            ("settled", settled_offset),
            ("reversed", settled_offset + rng.randint(60, 1440)),
        ]
    return [("pending", pending_offset), ("settled", settled_offset)]


def _append_event(
    rows: list[dict[str, object]],
    rng: random.Random,
    logical_tx_id: uuid.UUID,
    processor_reference: str,
    src_account_id: uuid.UUID,
    dest_account_id: uuid.UUID | None,
    merchant_id: uuid.UUID | None,
    amount: float,
    currency: str,
    tx_type: str,
    event_status: str,
    event_time: datetime,
) -> None:
    row = {
        "event_id": uuid.uuid4(),
        "logical_tx_id": logical_tx_id,
        "processor_reference": processor_reference,
        "src_account_id": src_account_id,
        "dest_account_id": dest_account_id,
        "merchant_id": merchant_id,
        "amount": amount,
        "fee_amount": _fee_for(tx_type, amount, event_status),
        "currency": currency,
        "tx_type": tx_type,
        "event_status": event_status,
        "event_time": event_time,
        "ingested_at": event_time + timedelta(seconds=rng.randint(10, 540)),
    }
    rows.append(row)
    if rng.random() < 0.03:
        duplicate = dict(row)
        duplicate["event_id"] = uuid.uuid4()
        duplicate["ingested_at"] = row["ingested_at"] + timedelta(seconds=rng.randint(45, 240))
        rows.append(duplicate)


def _generate_transaction_events(
    rng: random.Random,
    users: list[dict[str, object]],
    accounts: list[dict[str, object]],
    merchants: list[dict[str, object]],
    logical_tx_count: int,
) -> list[dict[str, object]]:
    account_lookup = {str(account["account_id"]): account for account in accounts}
    user_lookup = {str(user["user_id"]): user for user in users}
    active_accounts = [account for account in accounts if account["status"] == "active"]
    merchant_ids = [merchant["merchant_id"] for merchant in merchants]
    event_rows: list[dict[str, object]] = []
    window_start = datetime(2024, 2, 1, 0, 0, 0)

    for _ in range(logical_tx_count):
        src_account = rng.choice(active_accounts)
        src_user = user_lookup[str(src_account["user_id"])]
        account_opened_at = datetime.strptime(str(src_account["opened_at"]), "%Y-%m-%d %H:%M:%S")
        base_time = max(account_opened_at, window_start) + timedelta(
            days=rng.randint(0, 440),
            minutes=rng.randint(0, 1439),
        )
        tx_type = _weighted_choice(
            rng,
            [
                ("card_purchase", 0.54),
                ("transfer", 0.26),
                ("cash_out", 0.12),
                ("card_refund", 0.08),
            ],
        )
        amount = _amount_for_type(rng, tx_type)
        currency = str(src_account["currency"])
        merchant_id = None
        dest_account_id = None

        if tx_type in {"card_purchase", "card_refund"}:
            merchant_id = rng.choice(merchant_ids)
        elif tx_type == "transfer":
            candidates = [account for account in active_accounts if account["account_id"] != src_account["account_id"]]
            dest_account_id = rng.choice(candidates)["account_id"]

        logical_tx_id = uuid.uuid4()
        sequence = _event_sequence(rng, tx_type)
        for status, offset_minutes in sequence:
            processor_reference = f"{logical_tx_id.hex[:12]}-{status}"
            _append_event(
                event_rows,
                rng,
                logical_tx_id=logical_tx_id,
                processor_reference=processor_reference,
                src_account_id=src_account["account_id"],
                dest_account_id=dest_account_id,
                merchant_id=merchant_id,
                amount=amount,
                currency=currency,
                tx_type=tx_type,
                event_status=status,
                event_time=base_time + timedelta(minutes=offset_minutes),
            )

        if bool(src_user["is_business"]) and rng.random() < 0.06:
            burst_amount = round(amount * rng.uniform(0.45, 0.9), 2)
            for burst_index in range(3):
                burst_tx_id = uuid.uuid4()
                burst_reference = f"{burst_tx_id.hex[:12]}-settled"
                _append_event(
                    event_rows,
                    rng,
                    logical_tx_id=burst_tx_id,
                    processor_reference=burst_reference,
                    src_account_id=src_account["account_id"],
                    dest_account_id=dest_account_id,
                    merchant_id=None,
                    amount=burst_amount,
                    currency=currency,
                    tx_type="transfer",
                    event_status="settled",
                    event_time=base_time + timedelta(minutes=burst_index * 8),
                )

    suspicious_accounts = rng.sample(active_accounts, k=min(18, len(active_accounts)))
    for account in suspicious_accounts:
        base_time = window_start + timedelta(days=rng.randint(30, 430), hours=rng.randint(0, 23))
        currency = str(account["currency"])
        for index in range(5):
            logical_tx_id = uuid.uuid4()
            candidates = [candidate for candidate in active_accounts if candidate["account_id"] != account["account_id"]]
            dest_account = rng.choice(candidates)
            _append_event(
                event_rows,
                rng,
                logical_tx_id=logical_tx_id,
                processor_reference=f"{logical_tx_id.hex[:12]}-settled",
                src_account_id=account["account_id"],
                dest_account_id=dest_account["account_id"],
                merchant_id=None,
                amount=round(rng.uniform(85, 140), 2),
                currency=currency,
                tx_type="transfer",
                event_status="settled",
                event_time=base_time + timedelta(minutes=index * 2),
            )

    anomaly_accounts = rng.sample(active_accounts, k=min(12, len(active_accounts)))
    for account in anomaly_accounts:
        repeated_amount = round(rng.uniform(220, 420), 2)
        currency = str(account["currency"])
        base_time = window_start + timedelta(days=rng.randint(50, 420), hours=rng.randint(0, 23))
        candidates = [candidate for candidate in active_accounts if candidate["account_id"] != account["account_id"]]
        for index in range(3):
            logical_tx_id = uuid.uuid4()
            dest_account = rng.choice(candidates)
            _append_event(
                event_rows,
                rng,
                logical_tx_id=logical_tx_id,
                processor_reference=f"{logical_tx_id.hex[:12]}-settled",
                src_account_id=account["account_id"],
                dest_account_id=dest_account["account_id"],
                merchant_id=None,
                amount=repeated_amount,
                currency=currency,
                tx_type="transfer",
                event_status="settled",
                event_time=base_time + timedelta(minutes=index * 7),
            )

    event_rows.sort(key=lambda row: (str(row["logical_tx_id"]), str(row["event_time"]), str(row["ingested_at"])))
    return event_rows


def build_practice_assets(
    base_dir: Path | None = None,
    *,
    seed: int = DEFAULT_SEED,
    user_count: int = DEFAULT_USER_COUNT,
    merchant_count: int = DEFAULT_MERCHANT_COUNT,
    logical_tx_count: int = DEFAULT_LOGICAL_TX_COUNT,
    force: bool = False,
) -> dict[str, int | str]:
    paths = resolve_paths(base_dir)
    paths.practice_data_dir.mkdir(parents=True, exist_ok=True)
    paths.artifacts_dir.mkdir(parents=True, exist_ok=True)

    if force:
        for table_name in ("users", "accounts", "merchants", "transaction_events"):
            target = paths.practice_data_dir / f"{table_name}.csv"
            if target.exists():
                target.unlink()

    rng = random.Random(seed)
    Faker.seed(seed)
    fake = Faker()

    users = _generate_users(rng, fake, user_count)
    accounts = _generate_accounts(rng, users)
    merchants = _generate_merchants(rng, fake, merchant_count)
    transaction_events = _generate_transaction_events(rng, users, accounts, merchants, logical_tx_count)

    _write_csv(paths.practice_data_dir / "users.csv", USER_FIELDS, users)
    _write_csv(paths.practice_data_dir / "accounts.csv", ACCOUNT_FIELDS, accounts)
    _write_csv(paths.practice_data_dir / "merchants.csv", MERCHANT_FIELDS, merchants)
    _write_csv(
        paths.practice_data_dir / "transaction_events.csv",
        TRANSACTION_EVENT_FIELDS,
        transaction_events,
    )

    manifest = {
        "seed": seed,
        "user_rows": len(users),
        "account_rows": len(accounts),
        "merchant_rows": len(merchants),
        "transaction_event_rows": len(transaction_events),
        "logical_transactions_requested": logical_tx_count,
    }
    paths.manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def initialize_duckdb(
    base_dir: Path | None = None,
    *,
    force: bool = False,
) -> Path:
    paths = resolve_paths(base_dir)
    if force and paths.duckdb_path.exists():
        paths.duckdb_path.unlink()
    paths.artifacts_dir.mkdir(parents=True, exist_ok=True)

    connection = duckdb.connect(str(paths.duckdb_path))
    try:
        connection.execute(paths.schema_path.read_text(encoding="utf-8"))
        for table_name in ("users", "accounts", "merchants", "transaction_events"):
            csv_path = (paths.practice_data_dir / f"{table_name}.csv").as_posix()
            connection.execute(
                f"""
                COPY {table_name}
                FROM '{csv_path}'
                (FORMAT CSV, HEADER, DELIMITER ',', NULLSTR '{NULL_TOKEN}');
                """
            )
    finally:
        connection.close()
    return paths.duckdb_path
