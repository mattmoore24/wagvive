/**
 * Wagvive product illustration generator.
 * Produces a cohesive set of branded product illustrations (SVG -> PNG).
 * Style: semi-flat vector, soft palette fields, consistent grounding shadow.
 */
const fs = require('fs');
const path = require('path');
const sharp = require('sharp');

const OUT = process.argv[2] || '.';

// ---- Brand tokens -------------------------------------------------------
const C = {
  sage: '#6B8F71',
  sageDark: '#54735A',
  sageLight: '#8FAD94',
  sagePale: '#C3D4C6',
  terra: '#E2795A',
  terraLight: '#EC9C83',
  terraPale: '#F5CDBF',
  charcoal: '#33332D',
  charcoalSoft: '#4A4A42',
  cream: '#F7F2E9',
  creamDark: '#E8DFCC',
  blue: '#9AAFAE',
  blueDark: '#7B9291',
  blueLight: '#B9C9C8',
  bluePale: '#D8E2E1',
  white: '#FFFFFF',
};

// Soft alternating backgrounds so the grid reads as one system
const BG = {
  cream: '#F7F2E9',
  sage: '#EDF2EE',
  blue: '#EBF1F0',
  warm: '#FAF0EA',
};

const W = 1400, H = 1400;
const CX = 700;          // horizontal centre

// Contact shadow: sits directly under the product's base so nothing floats.
const shadow = (rx, baseY, ry = 26, opacity = 0.12, cx = CX) =>
  `<ellipse cx="${cx}" cy="${baseY}" rx="${rx}" ry="${ry}" fill="${C.charcoal}" opacity="${opacity}"/>`;

const frame = (bg, body) => `<svg width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg">
<rect width="${W}" height="${H}" fill="${bg}"/>
${body}
</svg>`;

// ---- Product illustrations ---------------------------------------------
// Each returns markup drawn for a 1400x1400 box, product centred ~ (700, 640).

function slickerBrush() {
  return `
${shadow(150, 1062)}
<g>
  <!-- neck flaring from head down into the grip -->
  <path d="M${CX - 132} 700 L${CX + 132} 700 L${CX + 78} 872 L${CX - 78} 872 Z" fill="${C.sage}"/>
  <!-- handle -->
  <rect x="${CX - 78}" y="838" width="156" height="224" rx="74" fill="${C.sageDark}"/>
  <rect x="${CX - 52}" y="866" width="42" height="168" rx="21" fill="${C.sageLight}" opacity="0.45"/>
  <!-- head shell -->
  <rect x="${CX - 250}" y="368" width="500" height="352" rx="66" fill="${C.sage}"/>
  <rect x="${CX - 250}" y="368" width="500" height="352" rx="66" fill="none" stroke="${C.sageDark}" stroke-width="7"/>
  <!-- bristle bed -->
  <rect x="${CX - 205}" y="410" width="410" height="268" rx="42" fill="${C.cream}"/>
  <!-- bristle dots -->
  <g fill="${C.blueDark}" opacity="0.55">
    ${(() => { let d = ''; for (let r = 0; r < 6; r++) for (let c = 0; c < 10; c++) {
      const x = CX - 178 + c * 39.5, y = 442 + r * 41; d += `<circle cx="${x}" cy="${y}" r="6.5"/>`;
    } return d; })()}
  </g>
  <!-- retract button -->
  <rect x="${CX - 52}" y="742" width="104" height="42" rx="21" fill="${C.terra}"/>
  <rect x="${CX - 38}" y="754" width="76" height="8" rx="4" fill="${C.white}" opacity="0.75"/>
</g>`;
}

function shedGlove() {
  return `
${shadow(216, 972)}
<g>
  <!-- thumb: broad flat join against the body, tapering to a rounded tip -->
  <path d="M${CX - 150} 496
           C${CX - 296} 506 ${CX - 380} 570 ${CX - 384} 644
           C${CX - 388} 720 ${CX - 300} 760 ${CX - 150} 748 Z"
        fill="${C.sageDark}"/>
  <!-- mitt body: tapers slightly toward the cuff -->
  <path d="M${CX - 196} 470
           Q${CX - 220} 366 ${CX - 116} 352
           L${CX + 116} 352
           Q${CX + 220} 366 ${CX + 196} 470
           L${CX + 182} 828
           Q${CX + 178} 918 ${CX + 84} 918
           L${CX - 84} 918
           Q${CX - 178} 918 ${CX - 182} 828 Z"
        fill="${C.sage}"/>
  <!-- palm pad -->
  <path d="M${CX - 160} 424
           L${CX + 154} 424
           Q${CX + 174} 424 ${CX + 174} 466
           L${CX + 174} 802
           Q${CX + 174} 856 ${CX + 108} 856
           L${CX - 92} 856
           Q${CX - 160} 856 ${CX - 160} 802 Z"
        fill="${C.cream}"/>
  <!-- grip nubs -->
  <g fill="${C.blue}">
    ${(() => { let d = ''; for (let r = 0; r < 7; r++) for (let c = 0; c < 7; c++) {
      const x = CX - 128 + c * 46, y = 462 + r * 55; d += `<circle cx="${x}" cy="${y}" r="12"/>`;
    } return d; })()}
  </g>
  <!-- cuff -->
  <rect x="${CX - 200}" y="882" width="400" height="90" rx="45" fill="${C.terra}"/>
  <rect x="${CX - 200}" y="882" width="400" height="32" rx="16" fill="${C.terraLight}" opacity="0.6"/>
</g>`;
}

function wipesCanister() {
  return `
${shadow(196, 1012)}
<g>
  <!-- emerging wipe -->
  <path d="M${CX - 46} 352 Q${CX - 96} 250 ${CX - 8} 216 Q${CX + 84} 186 ${CX + 66} 300 L${CX + 52} 356 Z"
        fill="${C.white}"/>
  <path d="M${CX - 46} 352 Q${CX - 96} 250 ${CX - 8} 216 Q${CX + 84} 186 ${CX + 66} 300 L${CX + 52} 356 Z"
        fill="none" stroke="${C.bluePale}" stroke-width="6"/>
  <!-- lid -->
  <rect x="${CX - 210}" y="336" width="420" height="86" rx="30" fill="${C.sageDark}"/>
  <ellipse cx="${CX}" cy="336" rx="210" ry="52" fill="${C.sage}"/>
  <ellipse cx="${CX}" cy="336" rx="96" ry="24" fill="${C.sageDark}" opacity="0.5"/>
  <!-- body -->
  <path d="M${CX - 210} 412 L${CX - 210} 946 Q${CX - 210} 1010 ${CX - 146} 1010
           L${CX + 146} 1010 Q${CX + 210} 1010 ${CX + 210} 946 L${CX + 210} 412 Z"
        fill="${C.cream}"/>
  <path d="M${CX - 210} 412 L${CX - 210} 946 Q${CX - 210} 1010 ${CX - 146} 1010
           L${CX + 146} 1010 Q${CX + 210} 1010 ${CX + 210} 946 L${CX + 210} 412 Z"
        fill="none" stroke="${C.creamDark}" stroke-width="7"/>
  <!-- label band -->
  <rect x="${CX - 210}" y="560" width="420" height="250" fill="${C.sage}"/>
  <rect x="${CX - 132}" y="628" width="264" height="16" rx="8" fill="${C.cream}" opacity="0.92"/>
  <rect x="${CX - 100}" y="676" width="200" height="12" rx="6" fill="${C.cream}" opacity="0.6"/>
  <!-- pulse mark on label -->
  <polyline points="${CX - 92},744 ${CX - 44},744 ${CX - 20},706 ${CX + 8},782 ${CX + 34},736 ${CX + 56},744 ${CX + 92},744"
            fill="none" stroke="${C.terraLight}" stroke-width="11" stroke-linecap="round" stroke-linejoin="round"/>
</g>`;
}

function nailGrinder() {
  return `
${shadow(120, 988)}
<g>
  <!-- grinding head -->
  <ellipse cx="${CX}" cy="344" rx="106" ry="46" fill="${C.blueLight}"/>
  <rect x="${CX - 106}" y="344" width="212" height="74" fill="${C.blue}"/>
  <ellipse cx="${CX}" cy="418" rx="106" ry="44" fill="${C.blueDark}"/>
  <ellipse cx="${CX}" cy="340" rx="62" ry="26" fill="${C.charcoalSoft}" opacity="0.35"/>
  <!-- collar -->
  <rect x="${CX - 122}" y="418" width="244" height="46" rx="20" fill="${C.sageDark}"/>
  <!-- body -->
  <rect x="${CX - 116}" y="454" width="232" height="530" rx="112" fill="${C.sage}"/>
  <rect x="${CX - 84}" y="486" width="52" height="450" rx="26" fill="${C.sageLight}" opacity="0.45"/>
  <!-- LED ring -->
  <circle cx="${CX}" cy="596" r="46" fill="none" stroke="${C.cream}" stroke-width="10" opacity="0.85"/>
  <circle cx="${CX}" cy="596" r="20" fill="${C.terra}"/>
  <!-- speed pips -->
  <g fill="${C.cream}" opacity="0.8">
    <circle cx="${CX}" cy="706" r="9"/>
    <circle cx="${CX}" cy="748" r="9"/>
    <circle cx="${CX}" cy="790" r="9"/>
  </g>
  <!-- base cap -->
  <rect x="${CX - 116}" y="928" width="232" height="58" rx="29" fill="${C.sageDark}"/>
</g>`;
}

function coolingMat() {
  return `
${shadow(430, 950, 22)}
<g>
  <!-- mat slab, gentle perspective -->
  <path d="M${CX - 420} 706 L${CX + 420} 706 Q${CX + 470} 706 ${CX + 470} 756
           L${CX + 470} 858 Q${CX + 470} 946 ${CX + 372} 946
           L${CX - 372} 946 Q${CX - 470} 946 ${CX - 470} 858
           L${CX - 470} 756 Q${CX - 470} 706 ${CX - 420} 706 Z"
        fill="${C.blueDark}"/>
  <path d="M${CX - 430} 470 L${CX + 430} 470 Q${CX + 480} 470 ${CX + 480} 520
           L${CX + 480} 800 Q${CX + 480} 856 ${CX + 424} 856
           L${CX - 424} 856 Q${CX - 480} 856 ${CX - 480} 800
           L${CX - 480} 520 Q${CX - 480} 470 ${CX - 430} 470 Z"
        fill="${C.blue}"/>
  <!-- quilt grid -->
  <g stroke="${C.bluePale}" stroke-width="7" opacity="0.75" stroke-linecap="round">
    ${(() => { let d = '';
      for (let i = 1; i < 5; i++) { const y = 470 + i * 77; d += `<line x1="${CX - 452}" y1="${y}" x2="${CX + 452}" y2="${y}"/>`; }
      for (let i = 1; i < 6; i++) { const x = CX - 480 + i * 160; d += `<line x1="${x}" y1="498" x2="${x}" y2="828"/>`; }
      return d; })()}
  </g>
  <!-- gel sheen -->
  <path d="M${CX - 430} 470 L${CX + 120} 470 L${CX - 190} 856 L${CX - 424} 856
           Q${CX - 480} 856 ${CX - 480} 800 L${CX - 480} 520 Q${CX - 480} 470 ${CX - 430} 470 Z"
        fill="${C.white}" opacity="0.16"/>
  <!-- paw emboss -->
  <g fill="${C.bluePale}" opacity="0.95">
    <ellipse cx="${CX - 34}" cy="632" rx="21" ry="27" transform="rotate(-18 ${CX - 34} 632)"/>
    <ellipse cx="${CX + 6}" cy="614" rx="20" ry="26" transform="rotate(-5 ${CX + 6} 614)"/>
    <ellipse cx="${CX + 46}" cy="618" rx="20" ry="26" transform="rotate(9 ${CX + 46} 618)"/>
    <ellipse cx="${CX + 84}" cy="640" rx="21" ry="27" transform="rotate(20 ${CX + 84} 640)"/>
    <rect x="${CX - 30}" y="662" width="132" height="72" rx="36" />
  </g>
</g>`;
}

function waterBowl() {
  return `
${shadow(210, 1022)}
<g>
  <!-- outer bowl -->
  <path d="M${CX - 330} 566 L${CX + 330} 566 L${CX + 268} 946
           Q${CX + 258} 1006 ${CX + 190} 1006 L${CX - 190} 1006
           Q${CX - 258} 1006 ${CX - 268} 946 Z"
        fill="${C.cream}"/>
  <path d="M${CX - 330} 566 L${CX + 330} 566 L${CX + 268} 946
           Q${CX + 258} 1006 ${CX + 190} 1006 L${CX - 190} 1006
           Q${CX - 258} 1006 ${CX - 268} 946 Z"
        fill="none" stroke="${C.creamDark}" stroke-width="7"/>
  <!-- rim -->
  <ellipse cx="${CX}" cy="566" rx="330" ry="92" fill="${C.sage}"/>
  <ellipse cx="${CX}" cy="566" rx="286" ry="74" fill="${C.blueDark}"/>
  <!-- water -->
  <ellipse cx="${CX}" cy="574" rx="264" ry="66" fill="${C.blue}"/>
  <!-- floating disc -->
  <ellipse cx="${CX}" cy="560" rx="176" ry="46" fill="${C.cream}"/>
  <ellipse cx="${CX}" cy="552" rx="176" ry="46" fill="${C.white}"/>
  <ellipse cx="${CX}" cy="552" rx="120" ry="30" fill="${C.creamDark}" opacity="0.55"/>
  <!-- ripples -->
  <ellipse cx="${CX - 196}" cy="592" rx="42" ry="12" fill="none" stroke="${C.bluePale}" stroke-width="6" opacity="0.85"/>
  <ellipse cx="${CX + 200}" cy="586" rx="34" ry="10" fill="none" stroke="${C.bluePale}" stroke-width="6" opacity="0.85"/>
  <!-- non-slip base -->
  <rect x="${CX - 210}" y="994" width="420" height="30" rx="15" fill="${C.charcoalSoft}" opacity="0.28"/>
</g>`;
}

function slowFeeder() {
  return `
${shadow(240, 1000)}
<g>
  <!-- bowl wall -->
  <path d="M${CX - 372} 600 L${CX + 372} 600 L${CX + 300} 926
           Q${CX + 290} 986 ${CX + 218} 986 L${CX - 218} 986
           Q${CX - 290} 986 ${CX - 300} 926 Z"
        fill="${C.terraLight}"/>
  <!-- rim -->
  <ellipse cx="${CX}" cy="600" rx="372" ry="112" fill="${C.terra}"/>
  <ellipse cx="${CX}" cy="600" rx="326" ry="94" fill="${C.terraPale}"/>
  <!-- maze ridges -->
  <g fill="${C.terra}">
    <ellipse cx="${CX}" cy="600" rx="74" ry="22"/>
    <path d="M${CX - 232} 578 a232 66 0 0 1 154 -60 l0 34 a198 56 0 0 0 -122 48 Z"/>
    <path d="M${CX + 232} 622 a232 66 0 0 1 -154 60 l0 -34 a198 56 0 0 0 122 -48 Z"/>
  </g>
  <g fill="none" stroke="${C.terra}" stroke-width="26" stroke-linecap="round">
    <path d="M${CX - 250} 616 a250 72 0 0 0 208 62"/>
    <path d="M${CX + 250} 584 a250 72 0 0 0 -208 -62"/>
  </g>
  <!-- inner shading -->
  <ellipse cx="${CX}" cy="608" rx="326" ry="94" fill="${C.charcoal}" opacity="0.06"/>
  <!-- base -->
  <rect x="${CX - 236}" y="974" width="472" height="30" rx="15" fill="${C.charcoalSoft}" opacity="0.25"/>
</g>`;
}

function comfortBed() {
  return `
${shadow(430, 1000, 30)}
<g>
  <!-- outer plush rim -->
  <ellipse cx="${CX}" cy="760" rx="470" ry="270" fill="${C.sageDark}"/>
  <ellipse cx="${CX}" cy="726" rx="470" ry="270" fill="${C.sage}"/>
  <!-- scalloped plush texture on rim -->
  <g fill="${C.sageLight}" opacity="0.45">
    ${(() => { let d = ''; const n = 22;
      for (let i = 0; i < n; i++) { const a = (Math.PI * 2 * i) / n;
        const x = CX + Math.cos(a) * 400, y = 726 + Math.sin(a) * 228;
        d += `<ellipse cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" rx="46" ry="30"/>`; }
      return d; })()}
  </g>
  <!-- inner cushion -->
  <ellipse cx="${CX}" cy="748" rx="312" ry="168" fill="${C.creamDark}"/>
  <ellipse cx="${CX}" cy="734" rx="312" ry="168" fill="${C.cream}"/>
  <!-- cushion quilting -->
  <g stroke="${C.creamDark}" stroke-width="6" opacity="0.9" fill="none">
    <path d="M${CX - 210} 700 Q${CX} 762 ${CX + 210} 700"/>
    <path d="M${CX - 210} 766 Q${CX} 828 ${CX + 210} 766"/>
  </g>
</g>`;
}

// ---- Bundle compositions -----------------------------------------------
// Reuse the same drawings, scaled into a 2x2 arrangement.
function compose(items) {
  // 2x2 grid, centred on the canvas. Source drawings are centred near (700, 690).
  const s = 0.52;
  const SRC_CX = 700, SRC_CY = 690;
  const dx = 232, dy = 236;
  const targets = [
    { x: CX - dx, y: 700 - dy }, { x: CX + dx, y: 700 - dy },
    { x: CX - dx, y: 700 + dy }, { x: CX + dx, y: 700 + dy },
  ];
  return items.map((m, i) => {
    const t = targets[i];
    const tx = t.x - SRC_CX * s, ty = t.y - SRC_CY * s;
    return `<g transform="translate(${tx.toFixed(1)}, ${ty.toFixed(1)}) scale(${s})">${m}</g>`;
  }).join('\n');
}

// ---- Manifest -----------------------------------------------------------
const products = [
  { file: 'product-slicker-brush',   bg: BG.cream, art: slickerBrush },
  { file: 'product-shedding-gloves', bg: BG.sage,  art: shedGlove },
  { file: 'product-cleaning-wipes',  bg: BG.blue,  art: wipesCanister },
  { file: 'product-nail-grinder',    bg: BG.warm,  art: nailGrinder },
  { file: 'product-cooling-mat',     bg: BG.cream, art: coolingMat },
  { file: 'product-water-bowl',      bg: BG.sage,  art: waterBowl },
  { file: 'product-slow-feeder',     bg: BG.blue,  art: slowFeeder },
  { file: 'product-comfort-bed',     bg: BG.warm,  art: comfortBed },
  { file: 'bundle-grooming-kit',     bg: BG.sage,
    art: () => compose([slickerBrush(), shedGlove(), wipesCanister(), nailGrinder()]) },
  { file: 'bundle-comfort-kit',      bg: BG.blue,
    art: () => compose([coolingMat(), waterBowl(), slowFeeder(), comfortBed()]) },
];

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  for (const p of products) {
    const svg = frame(p.bg, p.art());
    const svgPath = path.join(OUT, p.file + '.svg');
    const pngPath = path.join(OUT, p.file + '.png');
    fs.writeFileSync(svgPath, svg);
    await sharp(Buffer.from(svg)).resize(1400, 1400).png({ quality: 92 }).toFile(pngPath);
    console.log('OK', p.file);
  }
  console.log('\nGenerated', products.length, 'illustrations ->', OUT);
})().catch(e => { console.error('ERR', e); process.exit(1); });
