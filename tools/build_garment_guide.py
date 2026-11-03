#!/usr/bin/env python3
"""Build a local, offline visual index of the complete garment draft sets."""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SETS = [
    ('preservation', '存护 · 囡囡体 S 胸', 'march-7th-preservation-bjd-1-4'),
    ('hunt', '巡猎 · 万代坐姿娃', 'march-7th-hunt-bandai-sitting-plush'),
]


def esc(value):
    return html.escape(str(value), quote=True)


def main():
    sections = []
    for key, title, slug in SETS:
        directory = ROOT / 'projects/honkai-star-rail' / slug / 'garment-pattern'
        manifest = json.loads((directory / 'pattern-manifest.json').read_text())
        base = '../' + directory.relative_to(ROOT).as_posix()
        pieces = manifest['pieces']
        if isinstance(pieces, dict):
            pieces = [dict(piece_id=k, **v) for k, v in pieces.items()]
        cards = []
        for piece in pieces:
            ident = piece.get('piece_id', piece.get('id'))
            svg = directory / 'pieces' / f'{ident}.svg'
            if not svg.exists():
                raise FileNotFoundError(svg)
            cards.append(f'''<a class="piece" href="{base}/pieces/{esc(ident)}.svg" target="_blank">
              <img src="{base}/pieces/{esc(ident)}.svg" loading="lazy" alt="{esc(piece['name'])}">
              <strong>{esc(ident)} · {esc(piece['name'])}</strong>
              <span>裁剪数量：{esc(piece.get('cut_count', '见衣片'))}　面料：{esc(piece.get('material', '见清单'))}</span>
              <small>点击查看带尺寸、缝线和裁边的原图</small></a>''')
        pdfs = sorted(directory.glob('*.pdf'))
        pdflinks = ' '.join(f'<a class="button" href="{base}/{esc(p.name)}">1:1 衣片 PDF</a>' for p in pdfs)
        notes = directory / 'assembly.md'
        if not notes.exists():
            notes = directory / 'README.md'
        basis = ('胸围 170、腰围 128、肩宽 86 mm 等来自已登记的商品标称；缺少的长度采用明确列出的试版假设。'
                 if key == 'preservation' else
                 '尚无万代娃体实测围度：本套使用独立列出的假设设计基准，可替换参数重出衣片；不是已确认适配万代的成衣版。')
        sections.append(f'''<section id="{key}" {'hidden' if key == 'hunt' else ''}>
          <div class="intro"><div><p class="eyebrow">完整服装试版 / v0.2 / mm</p><h2>{title}</h2>
          <p>{basis}</p></div><div class="actions">{pdflinks}<a class="button secondary" href="{base}/{notes.name}">尺寸与组装说明</a></div></div>
          <h3>每层衣服的外形与穿搭关系</h3>
          <a href="{base}/layers-overview.png" target="_blank"><img class="board" src="{base}/layers-overview.png" alt="{title}分层外形"></a>
          <h3>全套衣片总览</h3>
          <a href="{base}/pieces-overview.png" target="_blank"><img class="board" src="{base}/pieces-overview.png" alt="{title}完整衣片"></a>
          <h3>逐片查看 · {len(pieces)} 种版片</h3><p>前后片、袖片、裙片及贴边各自列出；裁几片、镜像还是对折，以单片标注为准。整套图不可统一缩放来调尺码。</p>
          <div class="grid">{''.join(cards)}</div></section>''')
    page = '''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>三月七 · 完整衣片与分层打版</title><style>
    :root{color-scheme:light;--ink:#24354b;--pink:#b85d83;--line:#dddfe5}*{box-sizing:border-box}body{margin:0;background:#f5f3f1;color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;line-height:1.65}
    main{max-width:1320px;margin:auto;padding:36px 28px 80px}header{border-bottom:1px solid var(--line);padding:0 0 24px}h1{font-size:34px;margin:6px 0 10px}h2{font-size:28px;margin:0}h3{font-size:23px;margin:32px 0 12px}.eyebrow{font-size:13px;letter-spacing:2px;color:var(--pink);margin:0}.notice{background:#fff0dd;border-left:4px solid #ba8a48;padding:14px 18px;font-size:15px}
    nav{display:flex;gap:12px;margin-top:22px;flex-wrap:wrap}button,.button{font:inherit;border:1px solid var(--ink);padding:10px 18px;border-radius:9px;text-decoration:none;background:var(--ink);color:white;cursor:pointer}button[aria-selected=false],.secondary{color:var(--ink);background:white}.intro{display:flex;align-items:center;justify-content:space-between;gap:24px;margin:30px 0}.intro p{max-width:760px}.actions{display:flex;flex-direction:column;gap:10px;min-width:190px}.board{display:block;max-width:100%;height:auto;background:white;border:1px solid var(--line);border-radius:12px}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:16px}.piece{display:flex;flex-direction:column;background:white;padding:15px;border:1px solid var(--line);border-radius:12px;text-decoration:none;color:var(--ink)}.piece:hover{border-color:var(--pink)}.piece img{width:100%;height:280px;object-fit:contain;background:#fcfcfc}.piece strong{margin-top:14px}.piece span,.piece small{font-size:13px;margin-top:6px}.piece small{color:#687385}footer{margin-top:40px;color:#687385;font-size:13px}[hidden]{display:none!important}@media(max-width:700px){main{padding:24px 14px}.intro{display:block}.actions{margin-top:18px}h1{font-size:28px}}
    </style></head><body><main><header><p class="eyebrow">MARCH 7TH / DOLL GARMENT WORKSHOP</p><h1>完整衣服，从每一层到每一片</h1>
    <p>分层前后外形、真实衣片轮廓、缝份、背部开合与尺寸集中在这里。原有纹样将按这些衣片试穿后的缝线重新定位。</p>
    <div class="notice">这是完整结构的数值试版，尚未实物试穿。PDF 按 100% / 实际大小输出并核对 50 mm 校准标尺；带尺寸与工艺线的衣片图用于打版，不作为布料印花图发送。</div>
    <nav role="tablist"><button role="tab" aria-selected="true" data-target="preservation">存护 · 四分 BJD</button><button role="tab" aria-selected="false" data-target="hunt">巡猎 · 坐姿玩偶</button></nav></header>'''
    page += ''.join(sections)
    page += '''<footer>后背魔术贴承担衣服开合；存护背蝶结采用可拆别针，固定在一侧承力区。先试坯确认轮廓，再按部位面料印样与定稿。</footer></main><script>
    for(const b of document.querySelectorAll('[data-target]'))b.addEventListener('click',()=>{for(const s of document.querySelectorAll('section'))s.hidden=s.id!==b.dataset.target;for(const t of document.querySelectorAll('[data-target]'))t.setAttribute('aria-selected',String(t===b));location.hash=b.dataset.target;});
    if(location.hash==='#hunt')document.querySelector('[data-target="hunt"]').click();
    </script></body></html>'''
    out = ROOT / 'docs/garment-guide.html'
    out.write_text(page)
    print(out)


if __name__ == '__main__':
    main()
