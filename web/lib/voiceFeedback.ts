// Web Speech API voice feedback with exponential backoff.
// Mirrors the Python VoiceFeedback + FeedbackEngine backoff logic.

const GLOBAL_COOLDOWN_MS  = 3000;
const BASE_COOLDOWN_MS    = 5000;
const MAX_COOLDOWN_MS     = 20000;
const SILENCE_ABOVE_ACC   = 95;

export class VoiceFeedback {
  private lastVoiceTime  = 0;
  private lastSpoken:  Record<string, number> = {};
  private speakCount:  Record<string, number> = {};
  private wasFailing:  Record<string, boolean> = {};

  speak(text: string, ruleId: string, accuracy: number): void {
    if (accuracy >= SILENCE_ABOVE_ACC) return;

    const now = Date.now();
    if (now - this.lastVoiceTime < GLOBAL_COOLDOWN_MS) return;

    const count    = this.speakCount[ruleId] ?? 0;
    const cooldown = Math.min(BASE_COOLDOWN_MS * 2 ** count, MAX_COOLDOWN_MS);
    const last     = this.lastSpoken[ruleId] ?? 0;
    if (now - last < cooldown) return;

    this.lastSpoken[ruleId]  = now;
    this.lastVoiceTime       = now;
    this.speakCount[ruleId]  = count + 1;

    if (typeof window === "undefined") return;
    const utt = new SpeechSynthesisUtterance(text);
    utt.rate   = 0.95;
    utt.volume = 1;
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utt);
  }

  /** Call when a rule transitions from failing to passing so backoff resets. */
  onRulePassed(ruleId: string): void {
    this.speakCount[ruleId] = 0;
    delete this.lastSpoken[ruleId];
  }

  updateRuleState(ruleId: string, failing: boolean): void {
    const wasFailing = this.wasFailing[ruleId] ?? false;
    if (wasFailing && !failing) this.onRulePassed(ruleId);
    this.wasFailing[ruleId] = failing;
  }
}
