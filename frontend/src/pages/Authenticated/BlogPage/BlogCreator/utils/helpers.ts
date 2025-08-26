import { ReportType } from '../types';

// Helper to determine report type from insight data and report_kind
export function determineReportType(period?: string, level?: string, kind?: string): ReportType | null {
  if (!period || !level) return null;

  const periodCapitalized = period.charAt(0).toUpperCase() + period.slice(1).toLowerCase(); // Daily, Weekly, Monthly
  const levelCapitalized = level.charAt(0).toUpperCase() + level.slice(1).toLowerCase(); // Village, District, ...

  if (kind && kind.toLowerCase().includes('activity')) {
    // For activity reports pattern: activity_reports.DailyVillageActivityReport
    return `activity_reports.${periodCapitalized}${levelCapitalized}ActivityReport` as ReportType;
  }

  // For regular reports pattern: report.VillageDailyReport
  return `report.${levelCapitalized}${periodCapitalized}Report` as ReportType;
}

// Format date helper
export function formatDate(dateStr?: string): string {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  return d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
}

// Content size map
export const SIZE_MAP: Record<string, { label: string; chars: number }> = {
  micro: { label: 'Micro', chars: 280 },
  short_essay: { label: 'Short Essay', chars: 3200 },
  article: { label: 'Article', chars: 12000 },
};

export const SIZE_ORDER = ['micro', 'short_essay', 'article'];

// Find appropriate preset for content length
export const findPresetForLength = (len: number): string => {
  for (const key of SIZE_ORDER) {
    if (SIZE_MAP[key].chars >= len) return key;
  }
  return 'article';
};

// Auto-expand textarea logic
export const adjustTextareaHeight = (el: HTMLTextAreaElement | null) => {
  if (!el) return;
  el.style.height = 'auto';
  el.style.height = `${el.scrollHeight + 2}px`;
};

// Scroll handling for focused elements
export const handleFocusScroll = (el: HTMLElement | null) => {
  if (!el) return;
  setTimeout(() => {
    try {
      const top = el.getBoundingClientRect().top + window.scrollY - 8;
      window.scrollTo({ top, behavior: 'smooth' });
    } catch (e) {
      console.error('Error scrolling to element:', e);
    }
  }, 160);
};