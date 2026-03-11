import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import get_sc_install_path

try:
    import scdatatools
    from scdatatools.sc import StarCitizen
except ImportError as e:
    print(f"scdatatools import failed: {e}")
    print("Install with: pip install scdatatools")
    sys.exit(1)

# Configuration
sc_path_obj = get_sc_install_path("LIVE")
if sc_path_obj is None:
    print("ERROR: Star Citizen LIVE installation not found")
    print("Set sc_base in config.ini if installed in a non-standard location.")
    sys.exit(1)

sc_path = str(sc_path_obj)

def main():
    print(f"Initializing StarCitizen at {sc_path}...")

    try:
        sc = StarCitizen(sc_path)
        print("Success!")

        # Try to access datacore via the API (not manual parsing)
        print("\nAccessing DataCore...")
        dc = sc.datacore
        print(f"DataCore type: {type(dc)}")

        # Try to list records
        if hasattr(dc, 'records'):
            print(f"Total records: {len(dc.records)}")

            # Search for shield components
            print("\nSearching for shield components...")
            shield_records = []

            for idx, record in enumerate(dc.records):
                try:
                    if hasattr(record, 'name') and 'Shield' in record.name and 'Gen' in record.name:
                        shield_records.append(record)

                        if len(shield_records) <= 3:
                            print(f"\nFound: {record.name}")
                            if hasattr(record, 'to_json') or hasattr(record, 'json'):
                                json_data = record.to_json() if hasattr(record, 'to_json') else record.json()
                                print(f"JSON available: {len(str(json_data))} chars")
                                print(f"Sample: {str(json_data)[:200]}...")
                            elif hasattr(record, '__dict__'):
                                print(f"Attributes: {list(record.__dict__.keys())}")

                except Exception:
                    pass

                # Limit search to first 1000 for speed
                if idx >= 1000:
                    break

            print(f"\nTotal shield components found (first 1000 records): {len(shield_records)}")

        else:
            print("No 'records' attribute found on datacore.")
            print(f"Available attributes: {dir(dc)}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
