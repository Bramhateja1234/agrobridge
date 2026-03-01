import polib
import os

hi_po_path = r"d:\formers platform\agro_platform\locale\hi\LC_MESSAGES\django.po"
te_po_path = r"d:\formers platform\agro_platform\locale\te\LC_MESSAGES\django.po"

translations = {
    "AgroBridge": {"hi": "एग्रोब्रिज", "te": "ఆగ్రో బ్రిడ్జ్"},
    "Browse Crops": {"hi": "फसलें ब्राउज़ करें", "te": "పంటలను బ్రౌజ్ చేయండి"},
    "About": {"hi": "हमारे बारे में", "te": "మా గురించి"}
}

def update_po(po_path, lang_code):
    if not os.path.exists(po_path):
        print(f"File not found: {po_path}")
        return
    
    po = polib.pofile(po_path, encoding='utf-8')
    existing_entries = {entry.msgid for entry in po}
    
    added_count = 0
    for msgid, translations_dict in translations.items():
        if msgid not in existing_entries:
            entry = polib.POEntry(
                msgid=msgid,
                msgstr=translations_dict[lang_code]
            )
            po.append(entry)
            added_count += 1
            
    if added_count > 0:
        po.save()
        print(f"Added {added_count} new translations to {lang_code}.")
    else:
        print(f"No new translations to add for {lang_code}.")

update_po(hi_po_path, "hi")
update_po(te_po_path, "te")
print("Done appending translations.")
