export const TYPE_COLORS: Record<string, string> = {
  destructive_action: "#e4572e",
  privilege_escalation: "#f3a712",
  sandbox_escape: "#d7263d",
  deception: "#8f2d56",
  resistance_to_correction: "#3f88c5",
  unauthorized_action: "#2e86ab",
  goal_persistence: "#5b8c5a",
  resource_acquisition: "#8367c7",
  harmless_malfunction: "#9aa5b1",
  insufficient_evidence: "#c9ced6",
};

export const SEV_COLORS: Record<number, string> = {
  1: "#3ecf8e",
  2: "#a3d9b1",
  3: "#f3a712",
  4: "#e4572e",
  5: "#d7263d",
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
