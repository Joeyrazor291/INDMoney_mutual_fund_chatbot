import subprocess
import sys
import os
from pathlib import Path

def run_script(script_path):
    print(f"\n{'='*20}")
    print(f"Running: {script_path}")
    print(f"{'='*20}")
    
    result = subprocess.run([sys.executable, script_path], capture_output=False)
    if result.returncode != 0:
        print(f"Error running {script_path}. Exiting.")
        sys.exit(1)

def main():
    # 1. Scrape (HTML)
    run_script("phase_1/scraper.py")
    
    # 2. Parse (JSON) — extracts all fields from __NEXT_DATA__
    run_script("phase_1/parser.py")
    
    # 3. Enrich with MFAPI data (scheme codes, ISIN, historical NAV)
    run_script("phase_1/mfapi_fetcher.py")
    
    # 4. Enrich with static metadata (taxation, SIP, redemption, guardrails)
    run_script("phase_1/static_metadata.py")
    
    # 5. Chunk & Store (Vector DB)
    run_script("phase_1/chunker.py")
    
    print("\n" + "*"*30)
    print("INGESTION PIPELINE COMPLETE!")
    print("*"*30)

if __name__ == "__main__":
    main()
