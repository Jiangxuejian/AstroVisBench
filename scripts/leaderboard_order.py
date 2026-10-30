"""One display order for chart, Markdown tables and machine-readable rows."""

GROUPS = [
    ('published-full', 'Full-432 · published reference', 'Full-432\npublished reference'),
    ('independent-full', 'Full-432 · independent no-tool', 'Full-432\nindependent · no-tool'),
    ('lite-v1-t1', 'Lite-72 v1 · T1 agents', 'Lite-72 v1\nT1 agents'),
    ('historical-v2-t1', 'Lite-72 v2 selection · historical inputs · T1 agents',
     'Lite-72 v2 selection\nhistorical · T1 agents'),
    ('historical-v2-recovery', 'Lite-72 v2 selection · historical inputs · recovery',
     'Lite-72 v2 selection\nhistorical · recovery'),
]


def group_id(row):
    if row['source'] == 'published-reference':
        return 'published-full'
    if 'recovery' in row.get('suite', ''):
        return 'historical-v2-recovery'
    if 'v2-selection' in row['id']:
        return 'historical-v2-t1'
    if row.get('suite') == 'Full-432':
        return 'independent-full'
    if row['id'] == 'claude-code-k3-lite72':
        return 'lite-v1-t1'
    raise ValueError(f"Declare suite/track grouping for new row: {row['id']}")


def ordered_rows(rows):
    # Current display excludes v1 but keeps its immutable audit/history.
    eligible = [row for row in rows if group_id(row) != 'lite-v1-t1']
    return sorted(eligible, key=lambda row: (
        row.get('correct_v') is None,
        -row['correct_v'] if row.get('correct_v') is not None else 0, row['id']))
