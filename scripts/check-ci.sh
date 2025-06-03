#!/bin/bash

# Check CI status for Tastory project

echo "🔍 Checking CI status..."

# Get the latest run
latest_run=$(gh api repos/OS366/Tastory/actions/runs?per_page=1 | python3 -c "
import json, sys
data = json.load(sys.stdin)
if 'workflow_runs' in data and data['workflow_runs']:
    r = data['workflow_runs'][0]
    status = r['status']
    conclusion = r.get('conclusion', 'in progress')
    name = r['name']
    branch = r['head_branch']
    
    # Status emoji
    if status == 'in_progress':
        emoji = '⏳'
    elif conclusion == 'success':
        emoji = '✅'
    elif conclusion == 'failure':
        emoji = '❌'
    else:
        emoji = '⚠️'
    
    print(f'{emoji} {name} [{branch}]')
    print(f'   Status: {status}')
    if conclusion and conclusion != 'None':
        print(f'   Result: {conclusion}')
    print(f'   URL: {r[\"html_url\"]}')
else:
    print('No workflow runs found')
")

echo "$latest_run"

# Option to open in browser
echo ""
read -p "Open in browser? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    gh run view --web
fi 