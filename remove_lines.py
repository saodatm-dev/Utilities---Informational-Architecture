import os

filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'utilities-payment-userflow.md')
with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Keep lines 1-393 (index 0-392) and lines 1034+ (index 1033+)
# This removes old API content (lines 394-1033)
out = lines[:393] + lines[1033:]

with open(filepath, 'w', encoding='utf-8') as f:
    f.writelines(out)

print(f"Done. Removed {len(lines) - len(out)} lines. New total: {len(out)}")
