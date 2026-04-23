with open(r'd:\agro_platform\templates\farmer\dashboard.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

def check_balance(start_ln, end_ln, name):
    chunk = "".join(lines[start_ln-1:end_ln])
    balance = chunk.count('<div') - chunk.count('</div>')
    print(f"Section {name} (Lines {start_ln}-{end_ln}): Balance = {balance}")
    if balance != 0:
        print(f"  ERROR: Internal div imbalance in {name}!")

# Audit internal balance of problematic sections
check_balance(507, 718, 'crop-prediction')
check_balance(719, 828, 'fert-advice')
check_balance(829, 877, 'disease-detection')
check_balance(878, 917, 'weather-forecast')
check_balance(918, 1002, 'rainfall-prediction')
check_balance(1003, 1090, 'yield-prediction')
check_balance(1091, 1104, 'news-feed')
check_balance(1106, 1223, 'profile')
