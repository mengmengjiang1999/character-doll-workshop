"""Read the shared per-piece material records; keep page and tables consistent."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_catalog():
    return json.loads((ROOT / 'docs/material-catalog.json').read_text())['groups']


def load_records(directory, pieces):
    data = json.loads((directory / 'piece-materials.json').read_text())
    records = {p['piece_id']: p for p in data['pieces']}
    expected = {p['piece_id'] for p in pieces}
    assert len(records) == len(data['pieces']), 'Duplicate material piece IDs'
    assert set(records) == expected, f'Material coverage mismatch: {set(records) ^ expected}'
    groups = load_catalog()
    for piece in pieces:
        record = records[piece['piece_id']]
        assert record['name'] == piece['name']
        assert record['uses'], piece['piece_id']
        for use in record['uses']:
            assert use['group'] in groups, use
            assert use['role'] and use['treatment'] and use['placement'], use
    return records


def gsm(group):
    target = group.get('target_gsm')
    if not target:
        return '克重按货号确认'
    if target[0] == target[-1]:
        return f'{target[0]} g/m²'
    return f'{target[0]}–{target[-1]} g/m²'


def material_name(use, groups):
    group = groups[use['group']]
    return f"{group['name']}（{use['group']}，目标 {gsm(group)}）"


def use_note(use):
    note = f"{use['treatment']}；{use['placement']}"
    if use.get('cut_count'):
        note += f"；裁 {use['cut_count']} 片"
    if use.get('optional'):
        note += '；试样后选用'
    return note
