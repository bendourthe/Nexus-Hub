import { describe, expect, it } from "vitest";
import {
  DISCRIMINATING_NON_LINUX_SHARE,
  OBSERVATION_TOLERANCE,
  classifyObservation,
  nonLinuxShare,
  summarize,
  type Observation
} from "../src/providers/reconciliation";

/**
 * These tests exist to prove the classifier refuses the specific mistake that caused
 * two prior revisions of the drawdown model: treating a saturated meter as a
 * measurement, and treating a Linux-dominated month as agreement.
 */

function observation(overrides: Partial<Observation> = {}): Observation {
  return {
    month: "2026-08",
    displayedValue: 2000,
    displayedIsSaturated: true,
    allowance: 2000,
    predicted: 2595,
    mixByOs: { linux: 1457, windows: 312, macos: 826 },
    ...overrides
  };
}

describe("saturation-aware classification", () => {
  it("never lets a saturated month CONFIRM a model that predicts at or above the cap", () => {
    // August 2026, measured 2026-08-19: price-weighted 2,595 against a saturated
    // 2,000-minute meter. Consistent, and that is all. Every model predicting above
    // the cap produces exactly this display, so the month cannot choose between them.
    const result = classifyObservation(observation());
    expect(result.verdict).toBe("non-discriminating");
    expect(result.verdict).not.toBe("supports");
    expect(result.reason).toContain("consistent but not confirming");
  });

  it("refutes a model that predicts below a saturated cap", () => {
    // The unweighted model on the same month: 1,724 raw minutes. A model predicting
    // 1,724 cannot produce a meter pinned at 2,000. This is the falsification.
    const result = classifyObservation(observation({ predicted: 1724 }));
    expect(result.verdict).toBe("refutes");
    expect(result.reason).toContain("cannot produce a pinned meter");
  });

  it("refutes July 2026 for the unweighted model too", () => {
    // July 2026: 1,352.67 Linux + 195.6 Windows + 36 macOS private, saturated at the
    // 2,000 cap. Unweighted 1,584 is below the cap and therefore incompatible.
    const july = observation({
      month: "2026-07",
      predicted: 1584,
      mixByOs: { linux: 1352.67, windows: 195.6, macos: 36 }
    });
    expect(classifyObservation(july).verdict).toBe("refutes");
  });

  it("classifies a Linux-dominated month as non-discriminating even when the numbers match exactly", () => {
    // The Aug 1-10 window: 126 Linux + 4 Windows, roughly 3% non-Linux. It matched
    // the unweighted model precisely and was cited as support for it. It is not
    // support for anything - every candidate weighting lands inside tolerance here.
    const window = observation({
      month: "2026-08 (1-10)",
      displayedValue: 126.7,
      displayedIsSaturated: false,
      predicted: 126.7,
      mixByOs: { linux: 126, windows: 4, macos: 0 }
    });
    const result = classifyObservation(window);
    expect(result.verdict).toBe("non-discriminating");
    expect(result.nonLinuxShare).toBeLessThan(DISCRIMINATING_NON_LINUX_SHARE);
    expect(result.reason).toContain("below the 15% bar");
  });

  it("supports only an unsaturated, genuinely mixed month within tolerance", () => {
    const mixed = observation({
      displayedValue: 1500,
      displayedIsSaturated: false,
      predicted: 1505,
      mixByOs: { linux: 900, windows: 300, macos: 300 }
    });
    const result = classifyObservation(mixed);
    expect(result.verdict).toBe("supports");
    expect(Math.abs(result.relativeDifference ?? 1)).toBeLessThanOrEqual(OBSERVATION_TOLERANCE);
  });

  it("refutes an unsaturated, mixed month that falls outside tolerance", () => {
    const mixed = observation({
      displayedValue: 1500,
      displayedIsSaturated: false,
      predicted: 1100,
      mixByOs: { linux: 900, windows: 300, macos: 300 }
    });
    expect(classifyObservation(mixed).verdict).toBe("refutes");
  });

  it("computes the non-Linux share, and treats an empty mix as zero rather than NaN", () => {
    expect(nonLinuxShare({ linux: 900, windows: 50, macos: 50 })).toBeCloseTo(0.1, 6);
    expect(nonLinuxShare({ linux: 0, windows: 0, macos: 0 })).toBe(0);
  });
});

describe("standing verdict across a ledger", () => {
  it("lets one refutation stand against any number of supporting months", () => {
    const entries = [
      classifyObservation(observation({ displayedValue: 1500, displayedIsSaturated: false, predicted: 1505, mixByOs: { linux: 900, windows: 300, macos: 300 } })),
      classifyObservation(observation({ predicted: 1724 }))
    ];
    expect(summarize(entries)).toBe("refuted");
  });

  it("reports UNTESTED, not supported, when every month was non-discriminating", () => {
    // The honest and common state for a Linux-dominated account. Reporting it as
    // "supported" is precisely how an untested table acquires false authority.
    const entries = [classifyObservation(observation()), classifyObservation(observation({ month: "2026-07" }))];
    expect(summarize(entries)).toBe("untested");
  });
});
