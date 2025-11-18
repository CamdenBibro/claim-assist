#!/usr/bin/env python3
"""
Claim Assist - LLM-powered insurance claim adjuster
Main entry point for processing insurance claims
"""

import argparse
import sys
from pathlib import Path

# Handle both direct execution and module execution
try:
    from .config import Config
    from .processors import ClaimProcessor
except ImportError:
    from config import Config
    from processors import ClaimProcessor


def print_summary(summary: dict) -> None:
    """Print claim processing summary"""
    print("\n" + "="*60)
    print("CLAIM SUMMARY")
    print("="*60)
    print(f"Total items:        {summary['total_items']}")
    print(f"Auto-approved:      {summary['auto_approved']} (${summary['auto_approved_value']:,.2f})")
    print(f"Needs review:       {summary['needs_review']} (${summary['review_value']:,.2f})")
    print(f"Total claim value:  ${summary['total_value']:,.2f}")
    print("="*60 + "\n")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Process insurance claims with LLM-powered pricing research"
    )
    parser.add_argument(
        "input_csv",
        help="Path to input CSV file with claim items"
    )
    parser.add_argument(
        "-o", "--output",
        default="claim_evaluation_results.csv",
        help="Output CSV file for all results (default: claim_evaluation_results.csv)"
    )
    parser.add_argument(
        "-r", "--review",
        default="items_for_human_review.csv",
        help="Output CSV file for items needing review (default: items_for_human_review.csv)"
    )
    parser.add_argument(
        "-t", "--threshold",
        type=int,
        default=100,
        help="Value threshold for deep research vs simple pricing (default: 100)"
    )
    parser.add_argument(
        "--api-key",
        help="Anthropic API key (can also use ANTHROPIC_API_KEY env var)"
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable caching of results"
    )

    args = parser.parse_args()

    # Validate input file exists
    if not Path(args.input_csv).exists():
        print(f"Error: Input file '{args.input_csv}' not found", file=sys.stderr)
        sys.exit(1)

    # Load configuration
    try:
        config = Config.from_env()

        # Override with command line arguments
        if args.api_key:
            config.anthropic_api_key = args.api_key
        if args.threshold:
            config.value_threshold = args.threshold
        if args.no_cache:
            config.enable_cache = False

        # Validate configuration
        config.validate()

    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        print("\nPlease set ANTHROPIC_API_KEY environment variable or use --api-key option")
        sys.exit(1)

    # Initialize processor
    print("Initializing Claim Assist processor...")
    processor = ClaimProcessor(config)

    # Process claims
    try:
        print(f"Processing claims from: {args.input_csv}")
        results_df = processor.process_spreadsheet(args.input_csv)

        # Get summary
        summary = processor.get_summary()
        print_summary(summary)

        # Export results
        processor.export_results(args.output, args.review)

        print("\nProcessing complete!")

    except Exception as e:
        print(f"Error processing claims: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
