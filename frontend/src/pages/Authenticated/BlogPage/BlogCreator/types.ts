export type BlogType =
  | 'journey'
  | 'successful_experience'
  | 'milestone'
  | 'report_insight'
  | 'failed_initiation'
  | 'consumption'
  | 'answering_question';

export type ContentType = 'micro' | 'short_essay' | 'article';

export type ReportType =
  | 'activity_reports.DailyVillageActivityReport'
  | 'activity_reports.WeeklyVillageActivityReport'
  | 'activity_reports.MonthlyVillageActivityReport'
  | 'activity_reports.DailySubdistrictActivityReport'
  | 'activity_reports.WeeklySubdistrictActivityReport'
  | 'activity_reports.MonthlySubdistrictActivityReport'
  | 'activity_reports.DailyDistrictActivityReport'
  | 'activity_reports.WeeklyDistrictActivityReport'
  | 'activity_reports.MonthlyDistrictActivityReport'
  | 'activity_reports.DailyStateActivityReport'
  | 'activity_reports.WeeklyStateActivityReport'
  | 'activity_reports.MonthlyStateActivityReport'
  | 'activity_reports.DailyCountryActivityReport'
  | 'activity_reports.WeeklyCountryActivityReport'
  | 'activity_reports.MonthlyCountryActivityReport'
  | 'report.VillageDailyReport'
  | 'report.VillageWeeklyReport'
  | 'report.VillageMonthlyReport'
  | 'report.SubdistrictDailyReport'
  | 'report.SubdistrictWeeklyReport'
  | 'report.SubdistrictMonthlyReport'
  | 'report.DistrictDailyReport'
  | 'report.DistrictWeeklyReport'
  | 'report.DistrictMonthlyReport'
  | 'report.StateDailyReport'
  | 'report.StateWeeklyReport'
  | 'report.StateMonthlyReport'
  | 'report.CountryDailyReport'
  | 'report.CountryWeeklyReport'
  | 'report.CountryMonthlyReport'
  | 'report.CumulativeReport'
  | 'report.OverallReport';

export interface BlogFormData {
  type: BlogType;
  content_type: ContentType;
  content: string;
  target_user?: number | null;
  milestone_id?: string | null;
  report_type?: ReportType | null;
  report_id?: string | null;
  url?: string | null;
  contribution?: string | null;
  questionid?: number | null;
  country_id?: number | null;
  state_id?: number | null;
  district_id?: number | null;
  subdistrict_id?: number | null;
  village_id?: number | null;
  target_details?: string | null;
  failure_reason?: string | null;
  userid: number | null;
}

export interface InsightData {
  geographical_entity?: { id: number; name: string; type: string };
  id?: string | number;
  level?: string;
  new_users?: number;
  active_users?: number;
  date?: string;
  period?: string;
  report_kind?: string;
  milestone_kind?: string;
  title?: string;
  text?: string;
  photo_id?: string | number;
  milestone_id?: string | null;
  type?: string | null;
}

export interface AddressOption {
  id: number;
  name: string;
}

export const reportTypeOptions: { value: ReportType; label: string }[] = [
  { value: 'activity_reports.DailyVillageActivityReport', label: 'Daily Village Activity Report' },
  { value: 'activity_reports.WeeklyVillageActivityReport', label: 'Weekly Village Activity Report' },
  { value: 'activity_reports.MonthlyVillageActivityReport', label: 'Monthly Village Activity Report' },
  { value: 'activity_reports.DailySubdistrictActivityReport', label: 'Daily Subdistrict Activity Report' },
  { value: 'activity_reports.WeeklySubdistrictActivityReport', label: 'Weekly Subdistrict Activity Report' },
  { value: 'activity_reports.MonthlySubdistrictActivityReport', label: 'Monthly Subdistrict Activity Report' },
  { value: 'activity_reports.DailyDistrictActivityReport', label: 'Daily District Activity Report' },
  { value: 'activity_reports.WeeklyDistrictActivityReport', label: 'Weekly District Activity Report' },
  { value: 'activity_reports.MonthlyDistrictActivityReport', label: 'Monthly District Activity Report' },
  { value: 'activity_reports.DailyStateActivityReport', label: 'Daily State Activity Report' },
  { value: 'activity_reports.WeeklyStateActivityReport', label: 'Weekly State Activity Report' },
  { value: 'activity_reports.MonthlyStateActivityReport', label: 'Monthly State Activity Report' },
  { value: 'activity_reports.DailyCountryActivityReport', label: 'Daily Country Activity Report' },
  { value: 'activity_reports.WeeklyCountryActivityReport', label: 'Weekly Country Activity Report' },
  { value: 'activity_reports.MonthlyCountryActivityReport', label: 'Monthly Country Activity Report' },

  { value: 'report.VillageDailyReport', label: 'Village Daily Report' },
  { value: 'report.VillageWeeklyReport', label: 'Village Weekly Report' },
  { value: 'report.VillageMonthlyReport', label: 'Village Monthly Report' },
  { value: 'report.SubdistrictDailyReport', label: 'Subdistrict Daily Report' },
  { value: 'report.SubdistrictWeeklyReport', label: 'Subdistrict Weekly Report' },
  { value: 'report.SubdistrictMonthlyReport', label: 'Subdistrict Monthly Report' },
  { value: 'report.DistrictDailyReport', label: 'District Daily Report' },
  { value: 'report.DistrictWeeklyReport', label: 'District Weekly Report' },
  { value: 'report.DistrictMonthlyReport', label: 'District Monthly Report' },
  { value: 'report.StateDailyReport', label: 'State Daily Report' },
  { value: 'report.StateWeeklyReport', label: 'State Weekly Report' },
  { value: 'report.StateMonthlyReport', label: 'State Monthly Report' },
  { value: 'report.CountryDailyReport', label: 'Country Daily Report' },
  { value: 'report.CountryWeeklyReport', label: 'Country Weekly Report' },
  { value: 'report.CountryMonthlyReport', label: 'Country Monthly Report' },
  { value: 'report.CumulativeReport', label: 'Cumulative Report' },
  { value: 'report.OverallReport', label: 'Overall Report' },
];