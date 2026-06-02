import re, os
api_calls = []
for root, dirs, files in os.walk('frontend/src'):
    for f in files:
        if not f.endswith(('.tsx', '.ts')): continue
        path = os.path.join(root, f)
        with open(path) as fh:
            content = fh.read()
        matches = re.findall(r"api\.(post|put|delete|patch)\(['\"]([^'\"]+)['\"]", content)
        for m in matches:
            api_calls.append((m[0].upper(), m[1], path))
for method, path, file in sorted(api_calls):
    print(f'{method} {path:40s}  ({file})')
