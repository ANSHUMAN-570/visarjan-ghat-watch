"""Write the canonical dataset and a validation report to data/processed/ (reproducible from data/raw/)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.data_loader import ROOT, load_dataset  # noqa: E402
from src.evidence import observation_rows  # noqa: E402


def main() -> None:
    df, issues, cfg = load_dataset()
    out = ROOT / "data" / "processed"
    out.mkdir(parents=True, exist_ok=True)
    observation_rows(df, cfg).to_csv(out / "observations_canonical.csv", index=False)
    lines = [f"rows: {len(df)}", f"status counts: {df['status'].value_counts().to_dict()}", f"issues: {len(issues)}"]
    lines += [f"[{i.severity}] {i.code}: {i.message}" for i in issues]
    (out / "validation_report.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
