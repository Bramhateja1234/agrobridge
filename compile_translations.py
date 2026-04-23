import os
from babel.messages.mofile import write_mo
from babel.messages.pofile import read_po

def compile_translations(project_root):
    locale_dir = os.path.join(project_root, "locale")
    
    for lang in ["hi", "te"]:
        po_path = os.path.join(locale_dir, lang, "LC_MESSAGES", "django.po")
        mo_path = os.path.join(locale_dir, lang, "LC_MESSAGES", "django.mo")
        if os.path.exists(po_path):
            with open(po_path, "rb") as f:
                catalog = read_po(f)
            with open(mo_path, "wb") as f:
                write_mo(f, catalog)
            print(f"Compiled {po_path} to {mo_path}")

if __name__ == "__main__":
    compile_translations("d:\\agro_platform")
