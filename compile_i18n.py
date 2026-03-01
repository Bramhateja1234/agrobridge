import polib
import os
from pathlib import Path

def compile_translations():
    base_dir = Path("d:/formers platform/agro_platform/locale")
    po_files = list(base_dir.glob("**/*.po"))
    
    if not po_files:
        print("No .po files found.")
        return

    for po_path in po_files:
        mo_path = po_path.with_suffix(".mo")
        try:
            po = polib.pofile(str(po_path))
            po.save_as_mofile(str(mo_path))
            print(f"Compiled: {po_path} -> {mo_path}")
        except Exception as e:
            print(f"Failed to compile {po_path}: {e}")

if __name__ == "__main__":
    compile_translations()
