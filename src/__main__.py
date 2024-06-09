""" Main entry point for the application """

import argparse
import asyncio
from .work_items import main

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fetch and process work items from DevOps"
    )
    parser.add_argument("--output_json", action="store_true", help="Output JSON files")
    parser.add_argument(
        "--output_folder", type=str, default=".", help="Folder to save JSON files"
    )

    args = parser.parse_args()

    asyncio.run(main(args.output_json, args.output_folder))
