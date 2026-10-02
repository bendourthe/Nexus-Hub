/**
 * After the user opens the reset page, refresh once sooner than the normal
 * interval so the dashboard catches up with a reset they just used. Pressing
 * the button again restarts the wait instead of stacking refreshes.
 */
export const EARLY_REFRESH_DELAY_MS = 60_000;

export class EarlyRefresh {
  private timer: ReturnType<typeof setTimeout> | undefined;

  constructor(
    private readonly refresh: () => unknown,
    private readonly delayMs: number = EARLY_REFRESH_DELAY_MS,
  ) {}

  schedule(): void {
    this.dispose();
    this.timer = setTimeout(() => {
      this.timer = undefined;
      void this.refresh();
    }, this.delayMs);
  }

  dispose(): void {
    if (this.timer !== undefined) {
      clearTimeout(this.timer);
      this.timer = undefined;
    }
  }
}
