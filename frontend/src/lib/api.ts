export type Island = {
  prosperity: number; cleanliness: number; infrastructure: number; health_index: number;
  level: number; buildings: string[]; weather: string; pollution: string; reasons?: string[]; savings_stage: number;
  milestones?: {savings_stage: number; next_name: string | null; next_target_kopecks: number | null;
    to_next_kopecks: number; savings_progress_percent: number; allocated_kopecks: number;
    risk_remaining_kopecks: number; risk_over_kopecks: number; risk_progress_percent: number};
  stats?: {budget_kopecks: number; remaining_kopecks: number; necessary_kopecks: number;
    wanted_kopecks: number; savings_kopecks: number; avoided_count: number; streak: number}
}
export type User = {id: number; nickname: string; birth_year: number; has_budget: boolean; is_demo: boolean;
  tutorial_choice: 'guide' | 'skip' | null; tutorial_completed: boolean}
export type Transaction = {id: number; amount_kopecks: number; type: string; category: string;
  comment: string | null; item_name: string | null; date: string; is_demo: boolean; entry_id: string | null}
export type ScoreDelta = {prosperity: number; cleanliness: number; infrastructure: number; health_index: number}
export type EntryReport = {entry_id: string; date: string; summary: string; before: ScoreDelta; after: ScoreDelta;
  delta: ScoreDelta; level_before: number; level_after: number; savings_stage_before: number;
  savings_stage_after: number; actions: {type: string; label: string; amount_kopecks: number;
    note: string; delta: ScoreDelta}[]}
export type Scenario = {played_today: number; daily_limit: number; next_available_at: string;
  scenario: {id: string; title: string; situation: string;
  options: {id: string; label: string; effects: number[]; consequence: string}[]} | null}
export type Friend = {id: number; nickname: string; status: string; incoming: boolean; friendship_id: number}
export const localDate = () => {const d = new Date(); return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`}

export const rub = (kopecks: number) => new Intl.NumberFormat('ru-RU').format(kopecks / 100) + ' ₽'

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('island-token')
  let response: Response
  try {
    response = await fetch('/api' + path, { ...options, headers: {
      'Content-Type': 'application/json', ...(token ? {Authorization: `Bearer ${token}`} : {}),
      ...options.headers,
    }})
  } catch {
    throw new Error('Нет связи с островом. Попробуй ещё раз.')
  }
  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    if (response.status === 401) localStorage.removeItem('island-token')
    throw new Error(typeof data.detail === 'string' ? data.detail : 'Не получилось выполнить действие')
  }
  return data as T
}
