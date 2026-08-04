/**
 * Remove third-party branding from supplier product photos.
 *
 * Rather than a flat patch (which leaves a visible rectangle on a shaded
 * surface), each row inside the target box is rebuilt by interpolating between
 * clean pixels sampled immediately left and right of the box on that same row.
 * That preserves the surface's vertical shading and its gentle horizontal
 * gradient, then a light blur on the seam blends it in.
 */
const sharp = require('sharp');

async function removeRegion(src, dst, box, opts = {}) {
  const pad = opts.pad ?? 22;      // how far outside the box to sample clean pixels
  const feather = opts.feather ?? 3;

  const img = sharp(src).removeAlpha();
  const { width, height } = await img.metadata();
  const { data } = await img.raw().toBuffer({ resolveWithObject: true });
  const px = Buffer.from(data);
  const at = (x, y) => (y * width + x) * 3;

  const avg = (x0, x1, y) => {
    let r = 0, g = 0, b = 0, n = 0;
    for (let x = Math.max(0, x0); x < Math.min(width, x1); x++) {
      const i = at(x, y); r += px[i]; g += px[i + 1]; b += px[i + 2]; n++;
    }
    return n ? [r / n, g / n, b / n] : [255, 255, 255];
  };

  for (let y = box.top; y < box.top + box.height; y++) {
    if (y < 0 || y >= height) continue;
    const L = avg(box.left - pad, box.left - 4, y);
    const R = avg(box.left + box.width + 4, box.left + box.width + pad, y);
    for (let x = box.left; x < box.left + box.width; x++) {
      if (x < 0 || x >= width) continue;
      const t = (x - box.left) / Math.max(1, box.width - 1);
      const i = at(x, y);
      px[i]     = Math.round(L[0] + (R[0] - L[0]) * t);
      px[i + 1] = Math.round(L[1] + (R[1] - L[1]) * t);
      px[i + 2] = Math.round(L[2] + (R[2] - L[2]) * t);
    }
  }

  // Rebuild, then soften just the patched area so its edges don't read as a rectangle.
  const base = sharp(px, { raw: { width, height, channels: 3 } });
  const grow = feather * 2;
  const softBox = {
    left: Math.max(0, box.left - grow),
    top: Math.max(0, box.top - grow),
    width: Math.min(width, box.width + grow * 2),
    height: Math.min(height, box.height + grow * 2),
  };
  // .png() is required: a raw-input pipeline returns headerless pixels,
  // which composite() cannot decode.
  const softened = await base.clone().extract(softBox).blur(feather).png().toBuffer();

  await sharp(px, { raw: { width, height, channels: 3 } })
    .composite([{ input: softened, left: softBox.left, top: softBox.top }])
    .jpeg({ quality: 95 })
    .toFile(dst);

  return { width, height, box };
}

(async () => {
  const dir = 'C:/Users/mattm/OneDrive/Claude Code/Pet Store/config/branding/cj-raw';
  // "els pet" wordmark + cat-ear "e" monogram on the bowl face (800x800 source)
  const res = await removeRegion(
    `${dir}/bowl_19.jpg`,
    `${dir}/bowl_19_clean.jpg`,
    { left: 496, top: 598, width: 74, height: 78 },
    { pad: 26, feather: 3 }
  );
  console.log('de-branded bowl_19 ->', JSON.stringify(res));
})().catch(e => { console.error('ERR', e); process.exit(1); });
