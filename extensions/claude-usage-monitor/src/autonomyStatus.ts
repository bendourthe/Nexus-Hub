export type AutonomyMode = "off" | "edits" | "full" | "expired" | "unavailable";

interface PlatformStatus {
  platform?: string;
  supported?: boolean;
  status?: string;
  tier?: string;
  remaining_seconds?: number | null;
}
interface StatusDocument {
  project?: string | null;
  note?: string;
  platforms?: PlatformStatus[];
}

export interface AutonomyPresentation {
  mode: AutonomyMode;
  text: string;
  tooltip: string;
  backgroundColor?: "statusBarItem.warningBackground" | "statusBarItem.errorBackground";
}

function formatRemaining(seconds: number | null | undefined): string {
  if (typeof seconds !== "number" || seconds <= 0) {
    return "";
  }
  const minutes = Math.max(1, Math.ceil(seconds / 60));
  const hours = Math.floor(minutes / 60);
  const remainder = minutes % 60;
  return hours > 0 ? `${hours}h${remainder > 0 ? ` ${remainder}m` : ""}` : `${minutes}m`;
}

export function unavailableAutonomyPresentation(detail = "Nexus-Hub CLI was not found on PATH."): AutonomyPresentation {
  return {
    mode: "unavailable",
    text: "$(shield) Autonomy: Unavailable",
    tooltip: `${detail} Re-run the Nexus-Hub installer to restore the autonomy command.`,
  };
}

export function parseAutonomyStatus(
  raw: string,
  platform: string,
): AutonomyPresentation {
  let document: StatusDocument;
  try {
    document = JSON.parse(raw) as StatusDocument;
  } catch {
    return unavailableAutonomyPresentation("Nexus-Hub returned invalid autonomy status.");
  }

  if (!document.project) {
    return {
      mode: "off",
      text: "$(shield) Autonomy: Off",
      tooltip: document.note ?? "Open a Git workspace to manage project-scoped autonomy.",
    };
  }

  const entry = document.platforms?.find((item) => item.platform === platform);
  if (!entry || entry.supported === false) {
    return unavailableAutonomyPresentation(
      `No verified project-scoped autonomy descriptor is available for ${platform}.`,
    );
  }

  if (entry.status === "expired") {
    return {
      mode: "expired",
      text: "$(shield) Autonomy: Expired",
      tooltip: "The autonomy TTL expired. Run the toggle to revert or choose a new tier.",
    };
  }

  if (entry.status !== "active") {
    return {
      mode: "off",
      text: "$(shield) Autonomy: Off",
      tooltip: "Project autonomy is verified off. Select to enable a time-limited tier.",
    };
  }

  const remaining = formatRemaining(entry.remaining_seconds);
  const suffix = remaining ? ` ${remaining}` : "";
  if (entry.tier === "full") {
    return {
      mode: "full",
      text: `$(shield) Autonomy: Full${suffix}`,
      tooltip: "Full autonomy is active. Approval prompts are removed while the deny hook remains armed.",
      backgroundColor: "statusBarItem.errorBackground",
    };
  }
  return {
    mode: "edits",
    text: `$(shield) Autonomy: Edits${suffix}`,
    tooltip: "Edits autonomy is active. File edits are accepted while shell commands still prompt.",
    backgroundColor: "statusBarItem.warningBackground",
  };
}
