import sys
import os
from pathlib import Path

# Add root to sys.path BEFORE importing anything from phase modules
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import logging
from phase_5.scheduler.tasks import daily_data_refresh

# Setup console logging for verification
root = logging.getLogger()
root.setLevel(logging.INFO)
# Clear existing handlers
for handler in root.handlers[:]:
    root.removeHandler(handler)
    
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
root.addHandler(handler)

if __name__ == "__main__":
    print(f"Manual Trigger for Phase 5 Data Refresh... (Root: {BASE_DIR})")
    
    try:
        daily_data_refresh()
        print("\nSUCCESS: Refresh completed.")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"\nFAILED: {str(e)}")
        sys.exit(1)
