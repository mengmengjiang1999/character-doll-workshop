#!/usr/bin/env python3
"""Preflight our textile proof exports; this does not validate real fabric or fit."""
from pathlib import Path
import hashlib
import io
import json
import xml.etree.ElementTree as ET

import fitz
from PIL import Image, ImageCms

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'exports/local/pdf-review'


def main():
    REVIEW.mkdir(parents=True, exist_ok=True)
    for directory in sorted((ROOT / 'projects/honkai-star-rail').glob('*/fabric-print')):
        manifest = json.loads((directory / 'manifest.json').read_text())
        report_file = directory / 'export-checks.json'
        report = json.loads(report_file.read_text())
        width, height = manifest['canvas_mm']
        expected = [round(mm / 25.4 * 300) for mm in (width, height)]
        master = next(directory.glob('*-print-master-v0.1.svg'))
        svg_files = [master, *sorted((directory / 'components').glob('*.svg'))]
        for file in svg_files:
            document = ET.fromstring(file.read_text())
            ids = [n.get('id') for n in document.iter() if n.get('id')]
            assert len(ids) == len(set(ids)), f'Duplicate SVG IDs: {file}'
            for node in document.iter():
                assert node.tag.split('}')[-1] not in {'image', 'text', 'script', 'foreignObject'}, file
                target = node.get('{http://www.w3.org/1999/xlink}href', node.get('href'))
                if target:
                    assert target.startswith('#') and target[1:] in ids, (file, target)
        for record in report['raster_outputs']:
            file = directory / record['file']
            with Image.open(file) as img:
                assert list(img.size) == expected, (file, img.size)
                assert img.mode == 'RGB', (file, img.mode)
                assert max(abs(v - 300) for v in img.info['dpi']) < 1, (file, img.info['dpi'])
                profile = ImageCms.ImageCmsProfile(io.BytesIO(img.info['icc_profile']))
                profile_name = ImageCms.getProfileDescription(profile).strip()
                assert 'srgb' in profile_name.lower(), (file, profile_name)
                record['icc_profile_description'] = profile_name
                record['sha256'] = hashlib.sha256(file.read_bytes()).hexdigest()
        pdf = directory / report['pdf']
        with fitz.open(pdf) as document:
            assert len(document) == 1, pdf
            page = document[0]
            actual_mm = [v / 72 * 25.4 for v in (page.rect.width, page.rect.height)]
            assert max(abs(a - b) for a, b in zip(actual_mm, (width, height))) < .01, actual_mm
            assert not page.get_images(), f'Unexpected embedded raster in vector PDF: {pdf}'
            assert not page.get_text().strip(), f'Unexpected visible text: {pdf}'
            assert len(page.get_drawings()) > 10, f'Missing vector artwork: {pdf}'
            page.get_pixmap(matrix=fitz.Matrix(1, 1), alpha=False).save(REVIEW / f'{directory.parent.name}.png')
            report['pdf_verified'] = {'pages': 1, 'page_mm': [round(x, 4) for x in actual_mm],
                'embedded_raster_images': 0, 'visible_text_characters': 0,
                'vector_drawing_count': len(page.get_drawings()),
                'sha256': hashlib.sha256(pdf.read_bytes()).hexdigest()}
        report['svg_verified_count'] = len(svg_files)
        report['pdf_status'] = 'Digital checks passed; PDF rendered for visual review. Fabric color and garment fit remain untested.'
        report_file.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
        print(f'{directory.parent.name}: {len(svg_files)} SVG, RGB/ICC/300ppi PNG+TIFF, single-page vector PDF verified')


if __name__ == '__main__':
    main()
