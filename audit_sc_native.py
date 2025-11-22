"""
Star Citizen Language Pack Auditor (Native Extraction)

Uses unp4k.exe and unforge.exe to extract component data from Data.p4k
and audit against the language pack naming conventions.
"""

import os
import sys
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional
import re

# Configuration
SC_INSTALL_PATH = r"C:\Program Files\Roberts Space Industries\StarCitizen\LIVE"
TOOLS_DIR = Path(__file__).parent / "tools"
EXTRACT_DIR = Path(__file__).parent / "extracted"
UNP4K_EXE = TOOLS_DIR / "unp4k.exe"
UNFORGE_EXE = TOOLS_DIR / "unforge.exe"


class ComponentData:
    """Represents a ship component with auditable fields."""
    def __init__(self, name: str, token: str, size: int, comp_type: str, grade: str, description_token: str = ""):
        self.name = name
        self.token = token
        self.size = size
        self.type = comp_type
        self.grade = grade
        self.description_token = description_token
        self.item_class = "Unknown" # Derived from description
    
    def __repr__(self):
        return f"Component({self.name}, Token={self.token}, Size={self.size}, Type={self.type}, Grade={self.grade}, Class={self.item_class})"


def find_sc_installation() -> Optional[Path]:
    """Find Star Citizen installation directory."""
    default_path = Path(SC_INSTALL_PATH)
    if default_path.exists():
        p4k_file = default_path / "Data.p4k"
        if p4k_file.exists():
            print(f"Found Star Citizen at: {default_path}")
            return default_path
    
    print("ERROR: Cannot find Star Citizen installation")
    print(f"Expected: {default_path}")
    return None


def extract_from_p4k(p4k_path: Path, filter_pattern: str, output_dir: Path) -> bool:
    """
    Extract files from Data.p4k using unp4k.exe
    """
    print(f"Extracting from P4K: {filter_pattern}...")
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Run unp4k.exe
    cmd = [str(UNP4K_EXE), str(p4k_path), filter_pattern]
    
    try:
        # Change to output directory for extraction
        original_cwd = os.getcwd()
        os.chdir(output_dir)
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout
        )
        
        os.chdir(original_cwd)
        
        if result.returncode != 0:
            print(f"ERROR: unp4k.exe failed with code {result.returncode}")
            print(result.stderr)
            return False
        
        print(f"Extraction complete.")
        return True
        
    except subprocess.TimeoutExpired:
        print("ERROR: Extraction timed out")
        return False
    except Exception as e:
        print(f"ERROR: Extraction failed: {e}")
        return False


def unforge_dcb(dcb_path: Path) -> bool:
    """
    Convert Game.dcb to XML files using unforge.exe
    """
    print(f"Converting DCB to XML: {dcb_path.name}...")
   
    cmd = [str(UNFORGE_EXE), str(dcb_path)]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes timeout (this can be slow)
        )
        
        if result.returncode != 0:
            print(f"ERROR: unforge.exe failed with code {result.returncode}")
            print(result.stderr)
            return False
        
        print("Conversion complete.")
        return True
        
    except subprocess.TimeoutExpired:
        print("ERROR: Unforge timed out")
        return False
    except Exception as e:
        print(f"ERROR: Unforge failed: {e}")
        return False


def parse_global_ini(ini_path: Path) -> Dict[str, str]:
    """
    Parse global.ini to build name token dictionary.
    """
    print(f"Parsing localization file: {ini_path.name}...")
    
    name_dict = {}
    
    try:
        # Try multiple encodings
        for encoding in ['utf-8', 'utf-16', 'latin-1']:
            try:
                with open(ini_path, 'r', encoding=encoding) as f:
                    for line in f:
                        line = line.strip()
                        
                        # Skip comments and empty lines
                        if not line or line.startswith(';') or line.startswith('#'):
                            continue
                        
                        # Parse key=value
                        if '=' in line:
                            key, value = line.split('=', 1)
                            name_dict[key.strip()] = value.strip()
                
                print(f"Loaded {len(name_dict)} localization entries (encoding: {encoding})")
                return name_dict
                
            except UnicodeDecodeError:
                continue
        
        print("ERROR: Could not decode global.ini with any encoding")
        return {}
        
    except Exception as e:
        print(f"ERROR: Failed to parse global.ini: {e}")
        return {}


def resolve_name_token(token: str, name_dict: Dict[str, str]) -> str:
    """
    Resolve a name token (e.g., @item_Name_FR76) to display name.
    """
    # Strip leading @ if present
    clean_token = token.lstrip('@')
    
    return name_dict.get(clean_token, token)


def extract_component_from_xml(xml_path: Path) -> Optional[ComponentData]:
    """
    Parses a component XML to extract Name, Size, Type, Grade, and Description Token.
    Returns None if the file is not a valid component or missing critical fields.
    """
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # 1. Find AttachDef (Critical for component stats)
        # Path: Components -> SAttachableComponentParams -> AttachDef
        attach_def = root.find(".//AttachDef")
        if attach_def is None:
            return None
            
        # 2. Extract Type and Filter
        comp_type = attach_def.get("Type")
        valid_types = ["Cooler", "PowerPlant", "Shield", "QuantumDrive"]
        if comp_type not in valid_types:
            return None
            
        # 3. Extract Size and Grade
        size_str = attach_def.get("Size")
        grade_val = attach_def.get("Grade")
        
        if not size_str or not grade_val:
            return None
            
        try:
            size = int(size_str)
        except ValueError:
            return None
            
        # Map numeric grade to letter if necessary (1=A, 2=B, 3=C, 4=D)
        grade_map = {"1": "A", "2": "B", "3": "C", "4": "D"}
        grade = grade_map.get(grade_val, grade_val) # Default to original if not 1-4
        
        # 4. Extract Name and Description Tokens
        # Path: Components -> SAttachableComponentParams -> AttachDef -> Localization
        localization = attach_def.find("Localization")
        if localization is None:
            return None
            
        name_token = localization.get("Name")
        if not name_token or not name_token.startswith("@"):
            return None
            
        description_token = localization.get("Description", "")
            
        # Create ComponentData (Name will be resolved later)
        return ComponentData("UNRESOLVED", name_token, size, comp_type, grade, description_token)
        
    except Exception as e:
        return None


def walk_component_xmls(libs_dir: Path, name_dict: Dict[str, str]) -> List[ComponentData]:
    """
    Walk the extracted XML directory and find all components.
    """
    components = []
    
    scitem_root = libs_dir / "foundry" / "records" / "entities" / "scitem"
    
    if not scitem_root.exists():
        print(f"WARNING: scitem directory not found at {scitem_root}")
        return []
    
    # Walk the entire scitem directory
    xml_count = 0
    print(f"Scanning {scitem_root}...")
    
    for xml_file in scitem_root.rglob("*.xml"):
        xml_count += 1
        
        # Filter by filename patterns to focus on relevant components
        filename_lower = xml_file.name.lower()
        if any(keyword in filename_lower for keyword in ['shield', 'power', 'cooler', 'quantum', 'shld', 'powr', 'cool', 'qdrv']):
            # Call with 1 arg
            component = extract_component_from_xml(xml_file)
            if component:
                components.append(component)
        
        # Progress indicator
        if xml_count % 1000 == 0:
            print(f"  Processed {xml_count} XML files, found {len(components)} components so far...")
    
    print(f"Scanned {xml_count} XML files total")
    return components


def audit_language_pack(components: List[ComponentData], language_pack_ini: Path) -> Dict:
    """
    Audit the language pack against extracted component data.
    """
    print(f"\nAuditing language pack: {language_pack_ini}")
    
    # Parse the language pack
    lang_pack = parse_global_ini(language_pack_ini)
    
    results = {
        'total_components': len(components),
        'mismatches': [],
        'missing': [],
        'correct': [],
        'placeholders_ignored': 0
    }
    
    for comp in components:
        # 1. Resolve Description to find Class
        desc_token = comp.description_token
        clean_desc_token = desc_token.lstrip('@')
        description_text = lang_pack.get(clean_desc_token, "")
        
        # Extract Class from description (e.g., "Class: Military")
        # Regex looks for "Class:" followed by whitespace and a word
        class_match = re.search(r"Class:\s*(\w+)", description_text, re.IGNORECASE)
        if class_match:
            comp.item_class = class_match.group(1).capitalize()
        else:
            comp.item_class = "Unknown"
            
        # 2. Determine Prefix based on Class
        # Map: Military->M, Civilian->C, Industrial->I, Stealth->S, Competition->R
        class_prefix_map = {
            'Military': 'M',
            'Civilian': 'C',
            'Industrial': 'I',
            'Stealth': 'S',
            'Competition': 'R', 
        }
        
        type_prefix = class_prefix_map.get(comp.item_class, 'C')
        
        # 3. Resolve Name
        clean_name_token = comp.token.lstrip('@')
        actual_name = lang_pack.get(clean_name_token)
        
        # Case-insensitive fallback for name lookup
        if not actual_name:
            for k, v in lang_pack.items():
                if k.lower() == clean_name_token.lower():
                    actual_name = v
                    clean_name_token = k
                    break
        
        # 4. Filter Placeholders
        if actual_name and ("PLACEHOLDER" in actual_name or "LOC_PLACEHOLDER" in actual_name):
            results['placeholders_ignored'] += 1
            continue
            
        if not actual_name:
            results['missing'].append({
                'component': comp.token,
                'expected': f"{type_prefix}{comp.size}{comp.grade} ...",
                'description_class': comp.item_class
            })
            continue

        # 5. Generate Expected Name
        # Format: [Prefix][Size][Grade] [Name]
        expected_code = f"{type_prefix}{comp.size}{comp.grade}"
        
        # Check if the actual name starts with the code
        if actual_name.startswith(expected_code):
             results['correct'].append({
                'component': comp.token,
                'expected': expected_code,
                'actual': actual_name,
                'key': clean_name_token
            })
        else:
            # It's a mismatch
            results['mismatches'].append({
                'component': comp.token,
                'expected': f"{expected_code} ...",
                'actual': actual_name,
                'key': clean_name_token,
                'detected_class': comp.item_class
            })
    
    return results


def print_audit_report(results: Dict):
    """Print a formatted audit report."""
    print("\n" + "=" * 60)
    print("AUDIT REPORT")
    print("=" * 60)
    
    print(f"\nTotal Components Scanned: {results['total_components']}")
    print(f"Correct Names: {len(results['correct'])}")
    print(f"Mismatches: {len(results['mismatches'])}")
    print(f"Missing from Language Pack: {len(results['missing'])}")
    print(f"Placeholders Ignored: {results['placeholders_ignored']}")
    
    if results['mismatches']:
        print("\n" + "-" * 60)
        print("MISMATCHES (First 20):")
        print("-" * 60)
        for item in results['mismatches'][:20]:
            print(f"\nComponent: {item['component']}")
            print(f"  Expected: {item['expected']}")
            print(f"  Actual:   {item['actual']}")
            print(f"  Key:      {item['key']}")
            print(f"  Class:    {item['detected_class']}")
    
    if results['missing']:
        print("\n" + "-" * 60)
        print("MISSING FROM LANGUAGE PACK (First 20):")
        print("-" * 60)
        for item in results['missing'][:20]:
            print(f"  {item['component']} -> {item['expected']}")


def main():
    print("=" * 60)
    print("Star Citizen Language Pack Auditor (Native Extraction)")
    print("=" * 60)
    
    # 1. Find SC installation
    sc_path = find_sc_installation()
    if not sc_path:
        return 1
    
    p4k_file = sc_path / "Data.p4k"
    
    # 2. Extract Game2.dcb (changed from Game.dcb for 4.4.0+)
    print("\n[Phase 1] Extracting Game2.dcb...")
    dcb_output = EXTRACT_DIR / "dcb"
    dcb_path = dcb_output / "Data" / "Game2.dcb"
    
    if dcb_path.exists():
        print(f"Game2.dcb already exists at {dcb_path}, skipping extraction.")
    else:
        if not extract_from_p4k(p4k_file, "Data/Game2.dcb", dcb_output):
            print("Trying Game.dcb instead...")
            if not extract_from_p4k(p4k_file, "Data/Game.dcb", dcb_output):
                return 1
    
    # 3. Extract global.ini
    print("\n[Phase 2] Extracting global.ini...")
    ini_output = EXTRACT_DIR / "localization"
    
    # Try primary path first
    if not extract_from_p4k(p4k_file, "Data/Libs/Localization/English/global.ini", ini_output):
        # Fallback: try alternate path
        print("Trying alternate path...")
        if not extract_from_p4k(p4k_file, "Data/Localization/english/global.ini", ini_output):
            print("WARNING: Could not extract global.ini")
    
    # 4. Convert Game2.dcb to XML
    print("\n[Phase 3] Converting DCB to XML...")
    dcb_file = dcb_output / "Data" / "Game2.dcb"
    if not dcb_file.exists():
        # Try alternate filename
        dcb_file = dcb_output / "Data" / "Game.dcb"
        if not dcb_file.exists():
            print(f"ERROR: Neither Game2.dcb nor Game.dcb found in {dcb_output / 'Data'}")
            return 1
    
    # Check if we already have extracted XMLs
    libs_dir = dcb_output / "Data" / "libs"
    if libs_dir.exists() and any(libs_dir.iterdir()):
        print(f"Found existing extracted data in {libs_dir}")
        print("Skipping unforge step...")
    else:
        if not unforge_dcb(dcb_file):
            return 1
    
    # Parse arguments
    import argparse
    parser = argparse.ArgumentParser(description='Star Citizen Language Pack Auditor')
    parser.add_argument('--version', default='4.4.0', help='Game version (e.g., 4.4.0)')
    parser.add_argument('--channel', default='PTU', help='Game channel (e.g., PTU, LIVE)')
    args, _ = parser.parse_known_args()

    # 5. Use language pack global.ini for name resolution
    print("\n[Phase 4] Loading localization data...")
    
    # Use the language pack's global.ini for name token resolution
    lang_pack_path = Path(__file__).parent / args.version / args.channel / "data" / "Localization" / "english" / "global.ini"
    
    if not lang_pack_path.exists():
        print(f"ERROR: Language pack not found at {lang_pack_path}")
        print(f"Please ensure your language pack is in the {args.version}/{args.channel}/data/Localization/english/ directory")
        return 1
    
    print(f"Using language pack at: {lang_pack_path}")
    name_dict = parse_global_ini(lang_pack_path)
    
    if not name_dict:
        print("ERROR: Failed to parse language pack")
        return 1
    
    # 6. Parse component XMLs
    print("\n[Phase 5] Parsing component XMLs...")
    libs_dir = dcb_output / "Data" / "libs"
    components = walk_component_xmls(libs_dir, name_dict)
    
    print(f"\nFound {len(components)} relevant components!")
    
    # 7. Audit the language pack (compare extracted game data vs language pack names)
    print("\n[Phase 6] Auditing language pack...")
    
    # We're auditing the same file we used for name resolution
    # This checks if the names are in the correct compact format
    audit_results = audit_language_pack(components, lang_pack_path)
    
    # Write report to file
    report_path = Path("final_audit_report.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        def log(msg=""):
            print(msg)
            f.write(msg + "\n")
            
        log("=" * 60)
        log("AUDIT REPORT")
        log("=" * 60)
        
        results = audit_results
        log(f"\nTotal Components Scanned: {results['total_components']}")
        log(f"Correct Names: {len(results['correct'])}")
        log(f"Mismatches: {len(results['mismatches'])}")
        log(f"Missing from Language Pack: {len(results['missing'])}")
        log(f"Placeholders Ignored: {results['placeholders_ignored']}")
        
        if results['mismatches']:
            log("\n" + "-" * 60)
            log("MISMATCHES (First 20):")
            log("-" * 60)
            for item in results['mismatches'][:20]:
                log(f"\nComponent: {item['component']}")
                log(f"  Expected: {item['expected']}")
                log(f"  Actual:   {item['actual']}")
                log(f"  Key:      {item['key']}")
                log(f"  Class:    {item['detected_class']}")
        
        if results['missing']:
            log("\n" + "-" * 60)
            log("MISSING FROM LANGUAGE PACK (First 20):")
            log("-" * 60)
            for item in results['missing'][:20]:
                log(f"  {item['component']} -> {item['expected']}")
                
    print(f"Report written to {report_path.absolute()}")
    
    print("\n" + "=" * 60)
    print("Audit complete!")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
