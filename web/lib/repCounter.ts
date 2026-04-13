type Phase = "IDLE" | "UP" | "DOWN";

export class RepCounter {
  private phase: Phase = "IDLE";
  private count = 0;
  private buf: number[] = [];
  private readonly smoothing: number;

  constructor(
    public readonly downThreshold: number,
    public readonly upThreshold: number,
    smoothing = 5,
  ) {
    this.smoothing = smoothing;
  }

  get reps() { return this.count; }
  get currentPhase() { return this.phase; }

  update(angle: number): boolean {
    this.buf.push(angle);
    if (this.buf.length > this.smoothing) this.buf.shift();
    const smooth = this.buf.reduce((a, b) => a + b, 0) / this.buf.length;

    let repCompleted = false;

    if (this.phase === "IDLE" && smooth >= this.upThreshold) {
      this.phase = "UP";
    } else if (this.phase === "UP" && smooth <= this.downThreshold) {
      this.phase = "DOWN";
    } else if (this.phase === "DOWN" && smooth >= this.upThreshold) {
      this.phase = "UP";
      this.count++;
      repCompleted = true;
    }

    return repCompleted;
  }

  progress(): number {
    if (!this.buf.length) return 0;
    const smooth = this.buf.reduce((a, b) => a + b, 0) / this.buf.length;
    const span = this.upThreshold - this.downThreshold;
    return Math.max(0, Math.min(1, (this.upThreshold - smooth) / (span + 1e-8)));
  }

  reset() {
    this.count = 0;
    this.phase = "IDLE";
    this.buf = [];
  }
}
