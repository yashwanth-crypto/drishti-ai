"""End-to-end demo: Module 1 (defect detection) -> Module 2 (Hindi alert).

Runs Module 1's inference script as a subprocess (keeping the two modules
decoupled, as they'll be in production), then feeds its JSON output into
generate_alert(). Emits one record in the shared dashboard event schema.

Usage:
    python src/demo_pipeline.py --image path/to/part.jpg
"""
import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from alerts import generate_alert

MODULE1_DIR = Path(__file__).parent.parent.parent / "module1_cv_defect"


def run_module1_inference(image_path: str) -> dict:
    result = subprocess.run(
        [
            sys.executable, "infer.py", "predict",
            "--checkpoint", "../models/casting_mobilenetv2.pt",
            "--image", str(Path(image_path).resolve()),
        ],
        cwd=MODULE1_DIR / "src",
        capture_output=True, text=True, check=True,
        encoding="utf-8",
    )
    return json.loads(result.stdout)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True)
    parser.add_argument("--part-id", default=None)
    args = parser.parse_args()

    inspection = run_module1_inference(args.image)
    alert_text = generate_alert(
        defect_code=inspection["defect_type"],
        confidence=inspection["confidence"],
        part_id=args.part_id,
        language="hi",
    )

    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "module": "1+2",
        "event_type": "inspection",
        "payload": {
            **inspection,
            "part_id": args.part_id,
            "alert_hi": alert_text,
        },
    }
    print(json.dumps(event, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
