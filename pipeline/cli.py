from __future__ import annotations

import argparse
from pathlib import Path

from pipeline.evaluate import main as evaluate_main
from pipeline.candidate_shard import main as candidate_shard_main
from pipeline.freeze import main as freeze_main
from pipeline.ingest import main as ingest_main
from pipeline.pilot_review_report import main as pilot_review_report_main
from pipeline.shards import merge_shards, validate_shard
from pipeline.review_shard import main as review_shard_main
from pipeline.io import load_json
from pipeline.verification import main as verify_main


def main() -> None:
    parser = argparse.ArgumentParser(prog="mat4person")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in (
        "ingest",
        "verify-quotes",
        "build-candidate-shard",
        "review-shard",
        "pilot-review-report",
        "evaluate",
        "freeze",
    ):
        subparsers.add_parser(name, add_help=False)
    validate_parser = subparsers.add_parser("validate-shard")
    validate_parser.add_argument("config", type=Path)
    validate_parser.add_argument("shard", type=Path)
    merge_parser = subparsers.add_parser("merge")
    merge_parser.add_argument("config", type=Path)
    merge_parser.add_argument("shards", type=Path)
    merge_parser.add_argument("output", type=Path)
    args, remaining = parser.parse_known_args()
    if args.command == "ingest":
        import sys
        sys.argv = ["mat4person ingest", *remaining]
        ingest_main()
    elif args.command == "verify-quotes":
        import sys
        sys.argv = ["mat4person verify-quotes", *remaining]
        verify_main()
    elif args.command == "build-candidate-shard":
        import sys
        sys.argv = ["mat4person build-candidate-shard", *remaining]
        candidate_shard_main()
    elif args.command == "review-shard":
        import sys
        sys.argv = ["mat4person review-shard", *remaining]
        review_shard_main()
    elif args.command == "pilot-review-report":
        import sys
        sys.argv = ["mat4person pilot-review-report", *remaining]
        pilot_review_report_main()
    elif args.command == "evaluate":
        import sys
        sys.argv = ["mat4person evaluate", *remaining]
        evaluate_main()
    elif args.command == "freeze":
        import sys
        sys.argv = ["mat4person freeze", *remaining]
        freeze_main()
    elif args.command == "validate-shard":
        validate_shard(load_json(args.shard), load_json(args.config))
        print(f"Valid shard: {args.shard}")
    elif args.command == "merge":
        report = merge_shards(args.config, args.shards, args.output)
        print(f"Merged {len(report['shards'])} shard(s) into {args.output}")


if __name__ == "__main__":
    main()
