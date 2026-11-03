#!/usr/bin/env node
/** Export our flat SVG artwork to colour proofs. No sewing geometry is added. */
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const sharp = require('sharp');
const { chromium } = require('playwright');
const { PDFDocument } = require('pdf-lib');
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const ppi = 300;
const folders = process.argv.length > 2 ? process.argv.slice(2) : [
  'projects/honkai-star-rail/march-7th-preservation-bjd-1-4/fabric-print',
  'projects/honkai-star-rail/march-7th-hunt-bandai-sitting-plush/fabric-print',
];

async function exportRaster(svgFile, width, height) {
  const base = svgFile.replace(/\.svg$/, '');
  const pixels = [width, height].map(mm => Math.round(mm / 25.4 * ppi));
  // Set explicit raster viewport pixels while keeping the millimetre viewBox.
  // This avoids physical-unit/DPI scaling differences between SVG backends.
  const original = await fs.readFile(svgFile, 'utf8');
  const rasterSvg = original.replace(/<svg\b[^>]*>/, tag => tag
    .replace(/\bwidth="[\d.]+mm"/, `width="${pixels[0]}px"`)
    .replace(/\bheight="[\d.]+mm"/, `height="${pixels[1]}px"`));
  const raster = sharp(Buffer.from(rasterSvg), { density: 72 })
    .resize(pixels[0], pixels[1], { fit: 'fill' })
    .flatten({ background: '#ffffff' }).removeAlpha()
    .toColourspace('srgb').withIccProfile('srgb').withMetadata({ density: ppi });
  await raster.clone().png({ compressionLevel: 9 }).toFile(`${base}-300ppi.png`);
  await raster.clone().tiff({ compression: 'lzw', predictor: 'horizontal',
    xres: ppi / 25.4, yres: ppi / 25.4 }).toFile(`${base}-300ppi.tiff`);
  await sharp(`${base}-300ppi.png`).resize({ width: 1200 }).png()
    .toFile(path.join(path.dirname(svgFile), 'preview-v0.1.png'));
  const check = [];
  for (const extension of ['png', 'tiff']) {
    const file = `${base}-300ppi.${extension}`;
    const meta = await sharp(file).metadata();
    if (meta.width !== pixels[0] || meta.height !== pixels[1] ||
        meta.hasAlpha || !meta.icc || Math.abs(meta.density - ppi) > 1 ||
        meta.space !== 'srgb') throw new Error(`Invalid output metadata: ${file}`);
    check.push({ file: path.basename(file), width_px: meta.width, height_px: meta.height,
      density_ppi: meta.density, color_space: meta.space, embedded_icc: !!meta.icc,
      alpha: meta.hasAlpha, bytes: (await fs.stat(file)).size });
  }
  return check;
}

let browser;
try {
  const launchOptions = { headless: true };
  if (process.env.PRINT_CHROME_PATH) launchOptions.executablePath = process.env.PRINT_CHROME_PATH;
  browser = await chromium.launch(launchOptions);
  for (const folder of folders) {
    const directory = path.join(root, folder);
    const candidates = (await fs.readdir(directory)).filter(name => /print-master-v0\.1\.svg$/.test(name));
    if (candidates.length !== 1) throw new Error(`Expected one master SVG in ${folder}`);
    const file = path.join(directory, candidates[0]);
    const svg = await fs.readFile(file, 'utf8');
    // The masters must be self-contained vector art with no labels or downloaded bitmaps.
    if (/<(?:text|image|script|foreignObject)\b/i.test(svg) || /(?:href|url)\s*[=(]\s*["']?https?:/i.test(svg)) {
      throw new Error(`Unexpected labels, scripts or external artwork: ${file}`);
    }
    const tag = svg.match(/<svg\b[^>]*>/)[0];
    const width = Number(tag.match(/\bwidth="([\d.]+)mm"/)[1]);
    const height = Number(tag.match(/\bheight="([\d.]+)mm"/)[1]);
    const manifest = JSON.parse(await fs.readFile(path.join(directory, 'manifest.json'), 'utf8'));
    if (JSON.stringify(manifest.canvas_mm) !== JSON.stringify([width, height])) {
      throw new Error(`Manifest dimensions do not match SVG: ${file}`);
    }
    const outputs = await exportRaster(file, width, height);
    const page = await browser.newPage();
    await page.route('**/*', route => route.abort());
    await page.setContent(`<!doctype html><html><head><meta charset="UTF-8"><style>
      @page { size: ${width}mm ${height}mm; margin: 0; }
      html,body { margin:0; padding:0; width:${width}mm; height:${height}mm; }
      * { -webkit-print-color-adjust:exact; print-color-adjust:exact; }
      svg { display:block; width:${width}mm; height:${height}mm; }
    </style></head><body>${svg.replace(/<\?xml[^>]*\?>/, '')}</body></html>`);
    // Some Chrome PDF builds omit repeated <use> instances. Expand those
    // references for PDF painting while leaving the editable source intact.
    await page.evaluate(() => {
      let count = 0;
      let use;
      while ((use = document.querySelector('body > svg > :not(defs) use, body > svg > use'))) {
        if (++count > 1000) throw new Error('SVG reference expansion exceeded limit');
        const ref = use.getAttribute('href') || use.getAttributeNS('http://www.w3.org/1999/xlink', 'href');
        const source = document.getElementById(ref.slice(1));
        if (!source || !ref.startsWith('#')) throw new Error(`Unknown SVG reference: ${ref}`);
        const group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        for (const attribute of use.attributes) {
          if (!['href', 'xlink:href'].includes(attribute.name)) group.setAttribute(attribute.name, attribute.value);
        }
        const clone = source.cloneNode(true);
        clone.removeAttribute('id');
        group.appendChild(clone);
        use.replaceWith(group);
      }
    });
    const pdf = file.replace(/\.svg$/, '-1to1.pdf');
    const rawPdf = await page.pdf({ printBackground: true, preferCSSPageSize: true,
      width: `${width}mm`, height: `${height}mm`, margin: { top: 0, right: 0, bottom: 0, left: 0 } });
    // Chrome rounds page boxes. Keep artwork at its authored scale and make
    // the page box exactly the requested millimetres, preserving the top edge.
    const document = await PDFDocument.load(rawPdf);
    if (document.getPageCount() !== 1) throw new Error(`Unexpected PDF page count: ${pdf}`);
    const pdfPage = document.getPage(0);
    const exactWidth = width / 25.4 * 72;
    const exactHeight = height / 25.4 * 72;
    const heightCorrection = exactHeight - pdfPage.getHeight();
    pdfPage.setSize(exactWidth, exactHeight);
    pdfPage.setCropBox(0, 0, exactWidth, exactHeight);
    pdfPage.translateContent(0, heightCorrection);
    document.setTitle(`${path.basename(file, '.svg')} | textile colour proof | ${width} x ${height} mm`);
    document.setSubject('Flat textile artwork for sample printing; garment placement not approved.');
    await fs.writeFile(pdf, await document.save());
    await page.close();
    const report = { canvas_mm: [width, height], nominal_ppi: ppi,
      note: 'Artwork sampling layout. Final garment placement, printer profile and fabric shrinkage are not approved.',
      raster_outputs: outputs, pdf: path.basename(pdf), pdf_page_mm: [width, height],
      pdf_status: 'Exported; validate page dimensions and inspect rendered proof separately.' };
    await fs.writeFile(path.join(directory, 'export-checks.json'), JSON.stringify(report, null, 2) + '\n');
    console.log(`${folder}: ${width} × ${height} mm, PNG/TIFF ${outputs[0].width_px} × ${outputs[0].height_px}px, PDF`);
  }
} finally {
  await browser?.close();
}
