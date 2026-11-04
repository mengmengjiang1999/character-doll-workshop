#!/usr/bin/env python3
"""Generate readable material records from the same data as the garment guide."""
import json
from material_records import ROOT, load_catalog, load_records, gsm, material_name, use_note
from build_garment_guide import SETS


def cell(value):
    return str(value).replace('|', '／').replace('\n', '<br>')


def main():
    groups = load_catalog()
    for _, title, slug in SETS:
        directory = ROOT / 'projects/honkai-star-rail' / slug / 'garment-pattern'
        pieces = json.loads((directory / 'pattern-manifest.json').read_text())['pieces']
        records = load_records(directory, pieces)
        lines = [f'# {title} · 逐片材质记录', '',
                 '每个衣片编号分别记录实际用布层次。以下为本轮拟采用的取样方案，尚未采购或完成实布验证；克重为选样目标，商品实例另见[材料目录](../../../../docs/material-catalog.md)。', '',
                 '材质细分以本表为最新依据；原结构清单的 material 字段保留早期概略分组，裁片数量和几何仍按原清单。局部辅衬按指定安装区域取料，不将整片面布重复裁成衬。', '',
                 '[返回带花纹打版册](../../../../docs/garment-guide.html) · [可编辑材质数据](piece-materials.json) · [衣片与裁剪数量](pattern-manifest.json)', '',
                 '| 编号／衣片 | 各层材质与用途 | 里布／辅衬安排 | 选择理由 |',
                 '| --- | --- | --- | --- |']
        for piece in pieces:
            r = records[piece['piece_id']]
            uses = '<br>'.join(cell(f"{u['role']}：{material_name(u, groups)}；{use_note(u)}") for u in r['uses'])
            notes = cell(r['lining_note']) + '<br>' + cell(r['interfacing_note'])
            lines.append(f"| **{piece['piece_id']}** {cell(piece['name'])}<br>{cell(piece['cut_count'])} | {uses} | {notes} | {cell(r['reason'])} |")
        (directory / 'piece-materials.md').write_text('\n'.join(lines) + '\n')
        print(f'{slug}: {len(records)} material records')

    lines = ['# 衣片用料目录', '',
             '与各项目 `piece-materials.json` 共用一份材质目录。组号用来分单取样，具体面布、里布、衬布安排以每个衣片的记录为准。目标克重是本项目的选样范围；商品的实际成分、克重及工艺以来源页面和最终货号为准。', '',
             '| 组号 | 材质 | 成分 | 目标克重 | 厂商实例 | 工艺／用途 | 来源 |',
             '| --- | --- | --- | --- | --- | --- | --- |']
    for ident, group in groups.items():
        sources = ' · '.join(f'[资料 {i+1}]({url})' for i, url in enumerate(group.get('source_urls', [])))
        example = group.get('supplier_example', {})
        exemplar = f"{example.get('name', '待确认')}，实标 {example.get('gsm', '待确认')} g/m²"
        lines.append(f"| {ident} | {cell(group['name'])} | {cell(group['fiber'])} | {gsm(group)} | {cell(exemplar)} | {cell(group['process'])}<br>{cell(group.get('notes', ''))} | {sources} |")
    lines += ['', '[原按部位选布调研](fabric-selection.md) · [存护 30 片记录](../projects/honkai-star-rail/march-7th-preservation-bjd-1-4/garment-pattern/piece-materials.md) · [巡猎 27 片记录](../projects/honkai-star-rail/march-7th-hunt-bandai-sitting-plush/garment-pattern/piece-materials.md)', '']
    (ROOT / 'docs/material-catalog.md').write_text('\n'.join(lines))


if __name__ == '__main__':
    main()
