"""Generate empty or sample ground truth CSV template for manual logging."""

import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Create a ground truth CSV template for a traffic video.")
    parser.add_argument("--output", "-o", default="data/ground_truth/template.csv", help="Output CSV path")
    parser.add_argument("--sample", action="store_true", help="Include sample annotated rows")
    args = parser.parse_args()

    out_p = Path(args.output)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    header = "timestamp_s,class_name,direction\n"
    content = header
    if args.sample:
        content += (
            "12.4,car,entry\n"
            "15.1,motorcycle,exit\n"
            "24.8,truck,entry\n"
            "30.2,car,exit\n"
            "45.0,bus,entry\n"
        )

    out_p.write_text(content, encoding="utf-8")
    print(f"Created ground truth template at: {out_p}")


if __name__ == "__main__":
    main()
