import sys
sys.path.insert(0, '.')
from pipeline.excel_parser import parse_screener_excel

result = parse_screener_excel('Suzlon Energy.xlsx', 'Suzlon Energy')
print("=== Parsed Output ===")
for k, v in sorted(result.items()):
    print(f"  {k:30s} = {v}")
