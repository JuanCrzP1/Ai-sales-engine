import type { Attention, AttentionSettings, AttentionView, HoursMode, HoursRange } from "../../repositories/attention";
import type { HttpClient } from "./httpClient";

interface AttentionPayload {
  hours_mode: HoursMode;
  team_hours: HoursRange[];
  timezone: string;
  reply_minutes: number;
  resume_after_minutes: number | null;
  email_enabled: boolean;
  email_to: string | null;
  updated_at: string | null;
  business_hours: HoursRange[];
  account_emails: string[];
  email_available: boolean;
  team_available_now: boolean;
  next_opening: string | null;
  options: { timezones: { id: string; label: string }[]; reply_minutes: number[]; resume_after_minutes: number[] };
}

function toView(payload: AttentionPayload): AttentionView {
  return {
    hoursMode: payload.hours_mode,
    teamHours: payload.team_hours,
    timezone: payload.timezone,
    replyMinutes: payload.reply_minutes,
    resumeAfterMinutes: payload.resume_after_minutes,
    emailEnabled: payload.email_enabled,
    emailTo: payload.email_to,
    updatedAt: payload.updated_at,
    businessHours: payload.business_hours,
    accountEmails: payload.account_emails,
    emailAvailable: payload.email_available,
    teamAvailableNow: payload.team_available_now,
    nextOpening: payload.next_opening,
    options: {
      timezones: payload.options.timezones,
      replyMinutes: payload.options.reply_minutes,
      resumeAfterMinutes: payload.options.resume_after_minutes,
    },
  };
}

/** Lo que se envía al guardar: los nombres de la API (los problemas por campo vuelven con estas rutas). */
export function attentionBody(settings: AttentionSettings) {
  return {
    hours_mode: settings.hoursMode,
    team_hours: settings.teamHours,
    timezone: settings.timezone,
    reply_minutes: settings.replyMinutes,
    resume_after_minutes: settings.resumeAfterMinutes,
    email_enabled: settings.emailEnabled,
    email_to: settings.emailTo?.trim() || null,
  };
}

/** `Attention` sobre la API del panel: `/api/businesses/{slug}/attention`. */
export function createApiAttention(http: HttpClient, slug: string): Attention {
  const base = `/businesses/${encodeURIComponent(slug)}/attention`;
  return {
    get: async () => toView(await http.get<AttentionPayload>(base)),
    save: async (settings) => toView(await http.put<AttentionPayload>(base, attentionBody(settings))),
    sendTestEmail: async () => (await http.post<{ sent_to: string[] }>(`${base}/test-email`)).sent_to,
  };
}
