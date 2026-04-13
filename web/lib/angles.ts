import type { Landmark } from "./landmarks";

type P = [number, number];

function toPx(lm: Landmark, w: number, h: number): P {
  return [lm.x * w, lm.y * h];
}

export function angleBetween(a: P, b: P, c: P): number {
  const ba: P = [a[0] - b[0], a[1] - b[1]];
  const bc: P = [c[0] - b[0], c[1] - b[1]];
  const dot = ba[0] * bc[0] + ba[1] * bc[1];
  const magBa = Math.sqrt(ba[0] ** 2 + ba[1] ** 2);
  const magBc = Math.sqrt(bc[0] ** 2 + bc[1] ** 2);
  const cos = dot / (magBa * magBc + 1e-8);
  return (Math.acos(Math.max(-1, Math.min(1, cos))) * 180) / Math.PI;
}

export function deviationFromVertical(a: P, b: P): number {
  const vec: P = [b[0] - a[0], b[1] - a[1]];
  const vert: P = [0, 1];
  const cos =
    (vec[0] * vert[0] + vec[1] * vert[1]) /
    (Math.sqrt(vec[0] ** 2 + vec[1] ** 2) + 1e-8);
  return (Math.acos(Math.abs(Math.max(-1, Math.min(1, cos)))) * 180) / Math.PI;
}

export function midpoint(a: P, b: P): P {
  return [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
}

// ── Named extractors (all return degrees) ────────────────────────────────────

export class AngleExtractor {
  private w: number;
  private h: number;
  private lms: Landmark[];

  constructor(landmarks: Landmark[], width = 1, height = 1) {
    this.lms = landmarks;
    this.w = width;
    this.h = height;
  }

  private px(idx: number): P {
    return toPx(this.lms[idx], this.w, this.h);
  }

  leftKnee   = () => angleBetween(this.px(23), this.px(25), this.px(27));
  rightKnee  = () => angleBetween(this.px(24), this.px(26), this.px(28));
  leftHip    = () => angleBetween(this.px(11), this.px(23), this.px(25));
  rightHip   = () => angleBetween(this.px(12), this.px(24), this.px(26));
  leftElbow  = () => angleBetween(this.px(11), this.px(13), this.px(15));
  rightElbow = () => angleBetween(this.px(12), this.px(14), this.px(16));
  leftShoulder  = () => angleBetween(this.px(13), this.px(11), this.px(23));
  rightShoulder = () => angleBetween(this.px(14), this.px(12), this.px(24));

  torsoLean(): number {
    const midSh  = midpoint(this.px(11), this.px(12));
    const midHip = midpoint(this.px(23), this.px(24));
    return deviationFromVertical(midSh, midHip);
  }

  shoulderSymmetry(): number {
    const ls = this.px(11);
    const rs = this.px(12);
    return (Math.atan2(rs[1] - ls[1], rs[0] - ls[0]) * 180) / Math.PI;
  }
}
