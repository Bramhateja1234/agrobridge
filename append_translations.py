import os

hi_po = r"d:\agro_platform\locale\hi\LC_MESSAGES\django.po"
te_po = r"d:\agro_platform\locale\te\LC_MESSAGES\django.po"

hi_strings = """
msgid "Service Hub Location"
msgstr "सेवा हब स्थान"

msgid "Service Performance"
msgstr "सेवा प्रदर्शन"

msgid "Delivery Agent Dashboard"
msgstr "डिलीवरी एजेंट डैशबोर्ड"
"""

te_strings = """
msgid "Service Hub Location"
msgstr "సేవా కేంద్రం స్థానం"

msgid "Service Performance"
msgstr "సేవా పనితీరు"

msgid "Delivery Agent Dashboard"
msgstr "డెలివరీ ఏజెంట్ డ్యాష్‌బోర్డ్"
"""

with open(hi_po, 'a', encoding='utf-8') as f:
    f.write(hi_strings)

with open(te_po, 'a', encoding='utf-8') as f:
    f.write(te_strings)
