import argparse
import json
from dotenv import load_dotenv
from langfuse import get_client


def main() -> None:
    parser = argparse.ArgumentParser(description="Export the last N Langfuse traces as JSON.")
    parser.add_argument("-n", "--num-traces", type=int, default=10, help="How many latest traces to fetch")
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="Optional output file path. If omitted, prints JSON to stdout.",
    )
    parser.add_argument(
        "--environment",
        type=str,
        default=None,
        help="Optional Langfuse environment filter (e.g. default, production)",
    )
    args = parser.parse_args()

    load_dotenv()
    langfuse = get_client()

    if not langfuse.auth_check():
        raise SystemExit("Langfuse authentication failed. Check LANGFUSE_* env vars in .env")

    traces = langfuse.api.trace.list(
        limit=args.num_traces,
        order_by="timestamp.desc",
        environment=args.environment,
    )

    full_traces = [langfuse.api.trace.get(trace.id) for trace in traces.data]
    payload = {"count": len(full_traces), "traces": [trace.dict() for trace in full_traces]}

    json_output = json.dumps(payload, indent=2, default=str)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(json_output)
        print(f"Wrote {len(traces.data)} traces to {args.output}")
    else:
        print(json_output)


if __name__ == "__main__":
    main()
