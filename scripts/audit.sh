#!/bin/bash
echo "=== FILES ===" && find sim/ -name "*.py" 2>/dev/null | sort
echo "=== TESTS ===" && python -m pytest tests/ -v --tb=short 2>&1 | tail -30
echo "=== IMPORT ===" && python -c "import sim; print('OK')" 2>&1
echo "=== LINES ===" && find sim/ -name "*.py" -exec wc -l {} + 2>/dev/null | sort -n | tail -15
echo "=== TODOS ===" && grep -rn "TODO\|FIXME\|HACK" sim/ 2>/dev/null || echo "Clean"
echo "=== STATUS ===" && python -c "
import json; s=json.load(open('STATUS.json'))
print(f'Phase: {s[\"current_phase\"]}, Tests: {s[\"tests\"][\"passing\"]}/{s[\"tests\"][\"total\"]}')
print(f'Issues: {len(s[\"known_issues\"])}')
" 2>&1
