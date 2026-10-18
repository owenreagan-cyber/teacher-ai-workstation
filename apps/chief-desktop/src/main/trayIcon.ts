// Monochrome menu bar template image, drawn in code (no binary asset): an open ring, like a "C".
import { nativeImage, type NativeImage } from "electron";

export function trayTemplateImage(): NativeImage {
  const scale = 2;
  const size = 18 * scale;
  const buf = Buffer.alloc(size * size * 4); // BGRA, all transparent
  const c = (size - 1) / 2;
  const outer = 7.5 * scale;
  const inner = 4.6 * scale;
  for (let y = 0; y < size; y++) {
    for (let x = 0; x < size; x++) {
      const dx = x - c;
      const dy = y - c;
      const r = Math.hypot(dx, dy);
      const angle = Math.abs(Math.atan2(dy, dx)); // 0 = pointing right
      // Antialias the ring edges by one pixel; leave a 70° gap on the right.
      const edge = Math.min(r - inner, outer - r);
      if (edge <= -1 || angle < (35 * Math.PI) / 180) continue;
      const alpha = Math.round(255 * Math.min(1, edge + 1));
      buf[(y * size + x) * 4 + 3] = alpha; // black pixel with alpha
    }
  }
  const image = nativeImage.createFromBitmap(buf, { width: size, height: size, scaleFactor: scale });
  image.setTemplateImage(true);
  return image;
}
