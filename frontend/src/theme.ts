export const TYPE_COLORS: Record<string, string> = {
  destructive_action: "#ce2f00",
  privilege_escalation: "#c96f4a",
  sandbox_escape: "#e5484d",
  deception: "#a05195",
  resistance_to_correction: "#4c8dc9",
  unauthorized_action: "#2f9e9e",
  goal_persistence: "#5aa17f",
  resource_acquisition: "#8b6fd1",
  harmless_malfunction: "#7c8a8a",
  insufficient_evidence: "#94a3a1",
};

export const SEV_COLORS: Record<number, string> = {
  1: "#18b2ba",
  2: "#4aa0a6",
  3: "#c2603f",
  4: "#d24422",
  5: "#ce2f00",
};

export const INCIDENT_TYPES: Record<string, string> = {
  unauthorized_action: "Took an action it wasn't authorised to take.",
  resistance_to_correction: "Ignored or resisted instructions to stop.",
  deception: "Misrepresented what it did or was doing.",
  goal_persistence: "Kept pursuing a goal after it should have stopped.",
  privilege_escalation: "Gained access or permissions beyond what it was given.",
  sandbox_escape: "Broke out of its intended environment.",
  destructive_action: "Deleted, overwrote, or destroyed something.",
  resource_acquisition: "Acquired money, compute, or other resources.",
  harmless_malfunction: "A minor glitch with no real harm.",
  insufficient_evidence: "Not enough information to decide — the classifier abstained.",
};

export const typeColor = (t: string | null | undefined): string =>
  (t && TYPE_COLORS[t]) || "#6c757d";

export const sevColor = (s: number | null | undefined): string =>
  (s != null && SEV_COLORS[s]) || "#9aa5b1";

export function cleanText(s: string | null | undefined): string {
  if (!s) return "";
  const noTags = s.replace(/<[^>]+>/g, " ");
  const el = document.createElement("textarea");
  el.innerHTML = noTags;
  return el.value.replace(/\s+/g, " ").trim();
}
