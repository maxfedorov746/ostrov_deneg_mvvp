import {useEffect, useRef, useState, type FormEvent, type ReactNode} from 'react'
import {NavLink, Navigate, Route, Routes, useNavigate} from 'react-router-dom'
import {IslandView} from './components/IslandView'
import {Brand} from './components/Brand'
import {api, localDate, rub, type EntryReport, type Friend, type Island, type Scenario, type ScoreDelta, type Transaction, type User} from './lib/api'
import {useApp} from './lib/store'

function ErrorBox({message}: {message: string}) {return message ? <p className="error" role="alert">{message}</p> : null}
function Notice({message}: {message: string}) {return message ? <p className="notice" role="status">{message}</p> : null}

function Auth({sessionExpired = false}: {sessionExpired?: boolean}) {
  const navigate = useNavigate()
  const setUser = useApp(s => s.setUser)
  const [mode, setMode] = useState<'login'|'register'>(sessionExpired ? 'login' : 'register')
  const [nickname, setNickname] = useState('')
  const [contact, setContact] = useState('')
  const [password, setPassword] = useState('')
  const [birthYear, setBirthYear] = useState('')
  const [consent, setConsent] = useState(false)
  const [consentScreen, setConsentScreen] = useState(false)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const requiresConsent = Number(birthYear) >= new Date().getFullYear() - 18
  async function submit(event: FormEvent) {
    event.preventDefault(); setError('')
    if (mode === 'register' && requiresConsent && !consentScreen) {setConsentScreen(true); return}
    setBusy(true)
    try {
      const path = mode === 'register' ? '/auth/register' : '/auth/login'
      const body = mode === 'register' ? {nickname, contact, password, birth_year: Number(birthYear), parental_consent: consent} : {contact, password}
      const result = await api<{access_token: string; user: User}>(path, {method: 'POST', body: JSON.stringify(body)})
      localStorage.setItem('island-token', result.access_token)
      setUser(result.user)
      navigate(result.user.has_budget ? '/island' : '/onboarding')
    } catch (e) {setError((e as Error).message)} finally {setBusy(false)}
  }
  return <main className="auth-page"><div className="auth-hero"><Brand large/><p className="eyebrow">BERLOGATEAM / ИГРА О ВЫБОРЕ</p><h1>Твой план.<br/>Твой остров.</h1><p>Небольшие решения меняют целый мир.</p></div>
    <form className="card auth-card" onSubmit={submit}>
      {sessionExpired && <p className="notice" role="status">Прошлый вход больше не действует. Войди снова или создай новый остров.</p>}
      {consentScreen ? <><p className="eyebrow">ШАГ 2 ИЗ 2</p><h2>Согласие родителя</h2><p>Если тебе ещё нет 18 лет, попроси родителя или законного представителя прочитать этот текст. В MVP согласие отмечается здесь; в полноценной версии потребуется подтверждение.</p>
        <label className="check"><input type="checkbox" checked={consent} onChange={e => setConsent(e.target.checked)}/> Родитель или законный представитель согласен на создание аккаунта и обработку указанных данных.</label>
        <button className="primary" disabled={!consent || busy}>Создать остров</button><button type="button" className="text-button" onClick={() => setConsentScreen(false)}>Назад</button></>
      : <><h2>{mode === 'register' ? 'Создай свой остров' : 'С возвращением!'}</h2>
        {mode === 'register' && <><label>Никнейм<input value={nickname} onChange={e => setNickname(e.target.value)} minLength={3} maxLength={32} required placeholder="Например, Лисёнок"/></label>
          <label>Год рождения<input type="number" value={birthYear} onChange={e => setBirthYear(e.target.value)} min={new Date().getFullYear()-23} max={new Date().getFullYear()-14} required placeholder="2008"/></label></>}
        <label>Email или телефон<input value={contact} onChange={e => setContact(e.target.value)} required placeholder="you@example.ru"/></label>
        <label>Пароль<input type="password" value={password} onChange={e => setPassword(e.target.value)} minLength={8} required placeholder="От 8 символов"/></label>
        <button className="primary" disabled={busy}>{mode === 'register' ? 'Продолжить' : 'Войти'}</button>
        <button type="button" className="text-button" onClick={() => {setMode(mode === 'register' ? 'login' : 'register'); setError('')}}>{mode === 'register' ? 'Уже есть остров? Войти' : 'Нет острова? Зарегистрироваться'}</button></>}
      <ErrorBox message={error}/></form></main>
}

function Shell({children}: {children: ReactNode}) {
  const user = useApp(s => s.user)
  return <div className="shell"><header className="topbar"><Brand/><span className="nickname">{user?.nickname}</span></header><div className="page">{children}</div>
    {user?.has_budget && <nav className="bottom-nav" aria-label="Основная навигация">
      <NavLink to="/island"><b>01</b><span>Остров</span></NavLink><NavLink to="/history"><b>02</b><span>История</span></NavLink><NavLink to="/scenario"><b>03</b><span>Ситуация</span></NavLink><NavLink to="/friends"><b>04</b><span>Друзья</span></NavLink><NavLink to="/profile"><b>05</b><span>Профиль</span></NavLink>
    </nav>}</div>
}

function Onboarding() {
  const navigate = useNavigate(); const setUser = useApp(s => s.setUser); const user = useApp(s => s.user)
  const [amount, setAmount] = useState('6000'); const [target, setTarget] = useState('10'); const [error, setError] = useState('')
  async function submit(e: FormEvent) {e.preventDefault(); setError(''); try {
    await api('/budget', {method: 'PUT', body: JSON.stringify({amount_kopecks: Math.round(Number(amount)*100), savings_target_percent: Number(target)})})
    if (user) setUser({...user, has_budget: true}); navigate('/island')
  } catch (e) {setError((e as Error).message)}}
  return <Shell><div className="intro"><p className="eyebrow">ПЕРВЫЙ ШАГ</p><h1>Дай острову старт</h1><p>Сколько денег ты планируешь распределить в этом месяце? Это можно изменить позже.</p></div>
    <form className="card form-card" onSubmit={submit}><label>Бюджет на месяц, ₽<input type="number" min="1" step="0.01" value={amount} onChange={e => setAmount(e.target.value)} required/></label>
      <label>Хочу отложить, %<input type="number" min="0" max="50" value={target} onChange={e => setTarget(e.target.value)} required/></label><p className="hint">По умолчанию 10%. Даже маленькая сумма помогает.</p><button className="primary">Создать остров</button><ErrorBox message={error}/></form></Shell>
}

function Indicators({island}: {island: Island}) {
  return <div className="indicators">{[['01','Процветание',island.prosperity],['02','Чистота',island.cleanliness],['03','Инфраструктура',island.infrastructure],['04','Индекс здоровья',island.health_index]].map(([number,label,value]) =>
    <div className="indicator" key={String(label)}><span><em>{number}</em> {label}</span><strong>{value}</strong><div className="meter"><i style={{width: `${value}%`}}/></div></div>)}</div>
}

const scoreLabels: Record<keyof ScoreDelta, string> = {prosperity:'Процветание', cleanliness:'Чистота', infrastructure:'Инфраструктура', health_index:'Здоровье'}
function DeltaList({delta}: {delta: ScoreDelta}) {
  return <div className="delta-list">{(Object.keys(scoreLabels) as (keyof ScoreDelta)[]).map(key =>
    <span className={delta[key] > 0 ? 'up' : delta[key] < 0 ? 'down' : ''} key={key}>{scoreLabels[key]} <b>{delta[key] > 0 ? '+' : ''}{delta[key]}</b></span>)}</div>
}

function MilestonePanel({island}: {island: Island}) {
  const goal = island.milestones
  if (!goal) return null
  return <section className="milestone-grid" aria-label="Следующие изменения острова">
    <div className="card milestone-card"><div className="milestone-head"><span>01 / ОТКРЫТИЕ</span><strong>{goal.next_name || 'Все объекты открыты'}</strong></div>
      {goal.next_target_kopecks ? <><p>Следующая деталь появится, когда сбережения достигнут <b>{rub(goal.next_target_kopecks)}</b>.</p>
        <div className="goal-meter" role="progressbar" aria-label="До следующего объекта" aria-valuenow={goal.savings_progress_percent} aria-valuemin={0} aria-valuemax={100}><i style={{width:`${goal.savings_progress_percent}%`}}/></div>
        <small>Осталось отложить {rub(goal.to_next_kopecks)}</small></> : <p>Сад, теплица и маяк уже на острове. Поддерживай привычку откладывать.</p>}</div>
    <div className="card milestone-card risk"><div className="milestone-head"><span>02 / ЗАПАС ПЛАНА</span><strong>Граница перерасхода</strong></div>
      {goal.risk_over_kopecks > 0 ? <p>План превышен на <b>{rub(goal.risk_over_kopecks)}</b>. Это снижает показатели; спокойные новые записи и обновление плана помогут восстановиться.</p>
      : goal.risk_remaining_kopecks > 0 ? <p>До исчерпания плана осталось <b>{rub(goal.risk_remaining_kopecks)}</b>. Траты сверх бюджета начнут ухудшать остров.</p>
      : <p>План полностью распределён. Следующая трата создаст перерасход и начнёт снижать показатели.</p>}
      <div className="goal-meter" role="progressbar" aria-label="Использование бюджета" aria-valuenow={goal.risk_progress_percent} aria-valuemin={0} aria-valuemax={100}><i style={{width:`${goal.risk_progress_percent}%`}}/></div>
      <small>Сбережения тоже входят в распределённую часть бюджета. Желаемое может влиять на чистоту раньше.</small></div>
  </section>
}

function ReportPanel({report}: {report: EntryReport | null}) {
  return <section className="card report-card"><div className="section-heading"><div><p className="eyebrow">ПОСЛЕ ЗАПИСИ</p><h2>Отчёт об изменениях</h2></div><span>{report?.date || 'Ожидает записи'}</span></div>
    {report ? <><p className="report-summary">{report.summary}</p><DeltaList delta={report.delta}/>
      {report.level_after !== report.level_before && <p className="report-unlock">Уровень острова: {report.level_before} → {report.level_after}</p>}
      {report.savings_stage_after > report.savings_stage_before && <p className="report-unlock">На острове появилась новая деталь благодаря сбережениям.</p>}
      <div className="report-actions">{report.actions.map((action,index) => <div className="report-action" key={index}><span className="field-number">{String(index+1).padStart(2,'0')} / ДЕЙСТВИЕ</span><h3>{action.label}</h3><p>{action.note}</p><DeltaList delta={action.delta}/></div>)}</div></>
    : <p className="hint">После первой записи здесь появится подробный разбор каждого действия и его влияния на остров.</p>}</section>
}

function TransactionForm({onSaved}: {onSaved: (island: Island, explanation: string, report: EntryReport) => void}) {
  const [expense, setExpense] = useState(''); const [saving, setSaving] = useState(''); const [avoided, setAvoided] = useState('')
  const [avoidedName, setAvoidedName] = useState('')
  const [category, setCategory] = useState('necessary')
  const [comment, setComment] = useState(''); const [date, setDate] = useState(localDate())
  const [error, setError] = useState(''); const [busy, setBusy] = useState(false)
  async function submit(e: FormEvent) {e.preventDefault(); setError('')
    if (![expense, saving, avoided].some(value => Number(value) > 0)) {setError('Укажи хотя бы одну сумму'); return}
    if (Number(avoided) > 0 && !avoidedName.trim()) {setError('Напиши, от какой покупки воздержался(ась)'); return}
    if (avoidedName.trim() && !(Number(avoided) > 0)) {setError('Укажи сумму покупки, от которой воздержался(ась)'); return}
    setBusy(true)
    try {
      const result = await api<{island: Island; explanation: string; report: EntryReport}>('/transactions/batch', {method: 'POST', body: JSON.stringify({
        expense_kopecks: Math.round(Number(expense || 0)*100), expense_category: category,
        saving_kopecks: Math.round(Number(saving || 0)*100), avoided_kopecks: Math.round(Number(avoided || 0)*100),
        avoided_name: avoidedName.trim() || null, comment: comment || null, date,
      })})
    setExpense(''); setSaving(''); setAvoided(''); setAvoidedName(''); setComment(''); onSaved(result.island, result.explanation, result.report)
  } catch(e) {setError((e as Error).message)} finally {setBusy(false)}}
  return <form className="card form-card journal-form" onSubmit={submit}><div className="section-heading"><div><p className="eyebrow">ЖУРНАЛ / ОДИН РАЗ ЗА ПЕРИОД</p><h2>Что произошло?</h2></div><span>Все суммы можно внести вместе</span></div>
    <div className="journal-fields"><div className="journal-field"><span className="field-number">01 / РАСХОД</span><label>Потратил(а), ₽<input type="number" min="0" step="0.01" value={expense} onChange={e => setExpense(e.target.value)} placeholder="0"/></label>
      <label>На что?<select value={category} onChange={e => setCategory(e.target.value)}><option value="necessary">Необходимое</option><option value="wanted">Желаемое</option></select></label></div>
      <div className="journal-field"><span className="field-number">02 / ЦЕЛЬ</span><label>Отложил(а), ₽<input type="number" min="0" step="0.01" value={saving} onChange={e => setSaving(e.target.value)} placeholder="0"/></label><p>Помогает острову расти.</p></div>
      <div className="journal-field"><span className="field-number">03 / ПАУЗА</span><label>Воздержался от покупки<input value={avoidedName} onChange={e => setAvoidedName(e.target.value)} maxLength={100} required={Number(avoided) > 0} placeholder="Например, наушники"/></label>
        <label>Сумма, ₽<input type="number" min="0" step="0.01" value={avoided} onChange={e => setAvoided(e.target.value)} placeholder="0"/></label><p>Сумма останется в бюджете.</p></div></div>
    <div className="form-grid"><label>Дата<input type="date" value={date} max={localDate()} min={`${localDate().slice(0,7)}-01`} onChange={e => setDate(e.target.value)} required/></label>
      <label>Заметка ко всей записи <small>необязательно</small><input value={comment} onChange={e => setComment(e.target.value)} maxLength={240} placeholder="Например, после школы"/></label></div>
    <button className="primary" disabled={busy}>Сохранить запись</button><ErrorBox message={error}/></form>
}

function IslandPage() {
  const island = useApp(s => s.island); const setIsland = useApp(s => s.setIsland)
  const [report, setReport] = useState<EntryReport | null>(null)
  const impactRef = useRef<HTMLElement | null>(null)
  const [error, setError] = useState(''); const [notice, setNotice] = useState(''); const [anim, setAnim] = useState(false)
  useEffect(() => {
    api<Island>('/island').then(setIsland).catch(e => setError(e.message))
    api<EntryReport | null>('/island/last-report').then(setReport).catch(e => setError(e.message))
  }, [setIsland])
  function update(value: Island, message = 'Остров откликнулся на твой выбор!') {setIsland(value); setAnim(true); window.setTimeout(() => setAnim(false), 950); setNotice(message)}
  function saved(value: Island, _explanation: string, nextReport: EntryReport) {
    setIsland(value); setReport(nextReport); setNotice(''); setAnim(true)
    window.setTimeout(() => setAnim(false), 950)
    window.requestAnimationFrame(() => {
      impactRef.current?.scrollIntoView({behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block:'start'})
      impactRef.current?.focus({preventScroll:true})
    })
  }
  async function demo(path: string) {setError(''); try {
    const result = await api<{island: Island; message: string}>(path, {method: 'POST'}); update(result.island)
    setNotice(result.message)
  } catch(e) {setError((e as Error).message)}}
  return <Shell><div className="page-heading"><p className="eyebrow">АРХИПЕЛАГ / МОЙ МАРШРУТ</p><h1>Мой остров</h1><p>Маленькие действия меняют картину.</p></div>
    {island && <><div className={anim ? 'island-update' : ''}><IslandView island={island}/></div>
      <section className="impact-focus" ref={impactRef} tabIndex={-1} aria-label="Изменения показателей острова">
        {report && <div className="impact-banner"><span>ВАШЕ РЕШЕНИЕ / {report.date}</span><p>{report.summary}</p><DeltaList delta={report.delta}/></div>}
        <Indicators island={island}/></section>
      <MilestonePanel island={island}/>
      <section className="card insight"><span>ПОЧЕМУ ТАК</span><p>{island.reasons?.[0]}</p><small>Открыто: {island.buildings.join(', ')}</small>
        <details><summary>Все причины и подсказки</summary><ul>{island.reasons?.map((reason, index) => <li key={index}>{reason}</li>)}</ul>
          <p className="hint">Погода зависит от индекса здоровья, мусор — от чистоты, а здания открываются с ростом уровня.</p></details></section>
      <div className="balance card"><span>Осталось в плане</span><strong>{rub(island.stats?.remaining_kopecks ?? 0)}</strong><small>Серия записей: {island.stats?.streak ?? 0} дн.</small></div></>}
    <Notice message={notice}/><ErrorBox message={error}/><TransactionForm onSaved={saved}/><ReportPanel report={report}/>
    <div className="demo-actions"><button onClick={() => demo('/demo/fill')}>Заполнить демо-данными <span>↗</span></button></div></Shell>
}

function HistoryPage() {
  const [items, setItems] = useState<Transaction[]>([]); const [island, setIsland] = useState<Island | null>(null); const [error, setError] = useState('')
  useEffect(() => {Promise.all([api<Transaction[]>('/transactions'), api<Island>('/island')]).then(([a,b]) => {setItems(a); setIsland(b)}).catch(e => setError(e.message))}, [])
  const names: Record<string,string> = {necessary:'Необходимое',wanted:'Желаемое',savings:'Сбережения'}
  const groups = Array.from(items.reduce((map, item) => {
    const key = item.entry_id || `old-${item.id}`
    map.set(key, [...(map.get(key) || []), item]); return map
  }, new Map<string, Transaction[]>()).values())
  return <Shell><div className="page-heading"><p className="eyebrow">ЭТОТ МЕСЯЦ</p><h1>Твои записи</h1><p>Видно, куда двигался план.</p></div><ErrorBox message={error}/>
    {island && <><div className="stat-grid"><div className="card"><small>Необходимое</small><strong>{rub(island.stats?.necessary_kopecks ?? 0)}</strong></div><div className="card"><small>Желаемое</small><strong>{rub(island.stats?.wanted_kopecks ?? 0)}</strong></div><div className="card"><small>Отложено</small><strong>{rub(island.stats?.savings_kopecks ?? 0)}</strong></div><div className="card"><small>Осталось</small><strong>{rub(island.stats?.remaining_kopecks ?? 0)}</strong></div></div><p className="streak">Серия записей: {island.stats?.streak ?? 0} дн.</p></>}
    <section className="card list-card"><h2>История</h2>{groups.length ? groups.map(group => <div className="journal-entry" key={group[0].entry_id || group[0].id}><div className="entry-head"><strong>{group[0].date}</strong><small>{group[0].comment || 'Без заметки'}</small></div>
      {group.map(item => <div className="transaction" key={item.id}><span>{item.type === 'avoided_purchase' ? `Воздержался от покупки${item.item_name ? ': ' + item.item_name : ''}` : item.type === 'saving' ? 'Отложил(а)' : names[item.category]}</span><strong className={item.type === 'expense' ? '' : 'positive'}>{item.type === 'expense' ? '−' : item.type === 'saving' ? '+' : '○'} {rub(item.amount_kopecks)}</strong></div>)}</div>) : <p className="hint">Пока пусто. Первая запись оживит остров.</p>}</section></Shell>
}

function ScenarioPage() {
  const [data, setData] = useState<Scenario | null>(null); const [message, setMessage] = useState(''); const [error, setError] = useState(''); const [busy, setBusy] = useState(false)
  const [chosen, setChosen] = useState(false); const [now, setNow] = useState(Date.now())
  const refreshedAtZero = useRef(false)
  const setIsland = useApp(s => s.setIsland)
  useEffect(() => {api<Scenario>('/scenarios/current').then(setData).catch(e => setError(e.message))}, [])
  useEffect(() => {const timer = window.setInterval(() => setNow(Date.now()), 1000); return () => window.clearInterval(timer)}, [])
  async function next() {setError(''); setMessage(''); setChosen(false); try {setData(await api<Scenario>('/scenarios/current'))} catch(e) {setError((e as Error).message)}}
  async function choose(id: string) {if (!data?.scenario) return; setBusy(true); setError(''); try {
    const result = await api<{consequence: string; island: Island}>(`/scenarios/${data.scenario.id}/choose`, {method:'POST', body:JSON.stringify({option_id:id})})
    setIsland(result.island); setMessage(result.consequence); setChosen(true)
  } catch(e) {setError((e as Error).message)} finally {setBusy(false)}}
  const seconds = data ? Math.max(0, Math.ceil((new Date(data.next_available_at).getTime() - now) / 1000)) : 0
  const countdown = [Math.floor(seconds / 3600), Math.floor(seconds % 3600 / 60), seconds % 60].map(x => String(x).padStart(2,'0')).join(':')
  useEffect(() => {
    if (seconds > 0) refreshedAtZero.current = false
    if (data?.scenario === null && seconds === 0 && !refreshedAtZero.current) {
      refreshedAtZero.current = true
      api<Scenario>('/scenarios/current').then(setData).catch(e => setError(e.message))
    }
  }, [data?.scenario, seconds])
  return <Shell><div className="page-heading"><p className="eyebrow">ТРЕНИРОВКА РЕШЕНИЙ / ДО 4 В ДЕНЬ</p><h1>Ситуации</h1><p>Пробуй решения без риска для настоящих денег.</p></div><ErrorBox message={error}/>
    {data && <section className="card scenario-card"><div className="scenario-topline"><span>СИТУАЦИЯ {Math.min(data.played_today + 1, 4)} / 4</span><div className="scenario-progress">{[0,1,2,3].map(i => <i key={i} className={i < data.played_today + (chosen ? 1 : 0) ? 'done' : ''}/>)}</div></div>
      {data.scenario ? <><h2>{data.scenario.title}</h2><p>{data.scenario.situation}</p>
        {chosen ? <><p className="scenario-result">{message}</p><button className="primary next-scenario" onClick={next}>Следующая ситуация <span>→</span></button></>
        : <div className="choices">{data.scenario.options.map(option => <button disabled={busy} key={option.id} onClick={() => choose(option.id)}>{option.label}<span>→</span></button>)}</div>}
        <p className="hint">Выбор влияет на остров, но не списывает деньги.</p></>
      : <div className="scenario-limit"><span className="limit-number">04 / 04</span><h2>На сегодня всё</h2><p>Новые ситуации откроются завтра. Остров пока можно развивать записями.</p><div className="countdown"><small>ВОЗОБНОВЛЕНИЕ ЧЕРЕЗ</small><strong role="timer">{countdown}</strong></div></div>}</section>}</Shell>
}

function FriendsPage() {
  const [friends, setFriends] = useState<Friend[]>([]); const [nickname, setNickname] = useState(''); const [view, setView] = useState<{nickname:string; island:Island} | null>(null)
  const [error, setError] = useState(''); const [notice, setNotice] = useState('')
  async function refresh() {setFriends(await api<Friend[]>('/friends'))}
  useEffect(() => {refresh().catch(e => setError(e.message))}, [])
  async function request(e: FormEvent) {e.preventDefault(); setError(''); try {await api('/friends/requests', {method:'POST', body:JSON.stringify({nickname})}); setNickname(''); setNotice('Запрос отправлен'); await refresh()} catch(e) {setError((e as Error).message)}}
  async function accept(id: number) {try {await api(`/friends/requests/${id}/accept`, {method:'POST'}); await refresh()} catch(e) {setError((e as Error).message)}}
  async function open(id: number) {try {setView(await api<{nickname:string; island:Island}>(`/friends/${id}/island`))} catch(e) {setError((e as Error).message)}}
  return <Shell><div className="page-heading"><p className="eyebrow">ВМЕСТЕ ИНТЕРЕСНЕЕ</p><h1>Острова друзей</h1><p>Суммы и личные записи видны только владельцу.</p></div>
    <form className="card friend-form" onSubmit={request}><label>Найти по никнейму<input value={nickname} onChange={e => setNickname(e.target.value)} required placeholder="Никнейм друга"/></label><button className="primary">Отправить запрос</button></form>
    <Notice message={notice}/><ErrorBox message={error}/><section className="card list-card"><h2>Друзья</h2>{friends.length ? friends.map(friend => <div className="friend-row" key={friend.id}><div><strong>{friend.nickname}</strong><small>{friend.status === 'accepted' ? 'Можно посмотреть остров' : friend.incoming ? 'Ждёт твоего ответа' : 'Запрос отправлен'}</small></div>
      {friend.status === 'accepted' ? <button onClick={() => open(friend.id)}>Смотреть</button> : friend.incoming ? <button onClick={() => accept(friend.friendship_id)}>Принять</button> : null}</div>) : <p className="hint">Пока никого нет. Демо-кнопка добавит остров друга.</p>}</section>
    {view && <section className="card friend-island"><button className="text-button" onClick={() => setView(null)}>← К списку</button><h2>Остров: {view.nickname}</h2><IslandView island={view.island}/><p className="friend-score">Индекс здоровья: <strong>{view.island.health_index}/100</strong></p></section>}</Shell>
}

function ProfilePage() {
  const user = useApp(s => s.user); const logout = useApp(s => s.logout); const navigate = useNavigate()
  const [amount, setAmount] = useState(''); const [target, setTarget] = useState('10'); const [notice, setNotice] = useState(''); const [error, setError] = useState('')
  useEffect(() => {api<{amount_kopecks:number; savings_target_percent:number}>('/budget').then(b => {setAmount(String(b.amount_kopecks/100)); setTarget(String(b.savings_target_percent))}).catch(e => setError(e.message))}, [])
  async function save(e: FormEvent) {e.preventDefault(); setError(''); try {await api('/budget', {method:'PUT', body:JSON.stringify({amount_kopecks: Math.round(Number(amount)*100), savings_target_percent:Number(target)})}); setNotice('План обновлён')} catch(e) {setError((e as Error).message)}}
  return <Shell><div className="page-heading"><p className="eyebrow">НАСТРОЙКИ</p><h1>Твой профиль</h1><p>Привет, {user?.nickname}!</p></div><form className="card form-card" onSubmit={save}><h2>План на месяц</h2><label>Бюджет, ₽<input type="number" min="1" step="0.01" value={amount} onChange={e => setAmount(e.target.value)} required/></label><label>Доля сбережений, %<input type="number" min="0" max="50" value={target} onChange={e => setTarget(e.target.value)} required/></label><button className="primary">Сохранить</button><Notice message={notice}/><ErrorBox message={error}/></form>
    <section className="card privacy"><h2>Твои данные</h2><p>Друг видит только внешний вид острова и индекс здоровья. Суммы, записи и контакт ему недоступны.</p><button className="secondary" onClick={() => {logout(); navigate('/auth')}}>Выйти</button></section></Shell>
}

const tutorialSteps = [
  {number:'01', title:'Задай свой план', text:'Укажи бюджет на месяц и сумму, которую хочешь отложить. План можно изменить в профиле.'},
  {number:'02', title:'Записывай одним движением', text:'В одной форме можно указать трату, сбережение и покупку, от которой ты отказался. Дата и заметка будут общими.'},
  {number:'03', title:'Наблюдай за островом', text:'Записи меняют здания, чистоту и погоду. Под островом всегда есть объяснение и подсказка, что делать дальше.'},
  {number:'04', title:'Пробуй ситуации', text:'Выбирай решения в коротких историях. Доступно четыре ситуации в день; таймер покажет, когда откроются новые.'},
  {number:'05', title:'Смотри острова друзей', text:'Добавь друга по никнейму. Друг увидит только остров и индекс здоровья — твои суммы останутся личными.'},
]

function Tutorial() {
  const user = useApp(s => s.user); const setUser = useApp(s => s.setUser)
  const [step, setStep] = useState(0); const [busy, setBusy] = useState(false); const [error, setError] = useState('')
  if (!user || user.tutorial_completed) return null
  async function save(choice: 'guide'|'skip'|'complete') {
    setBusy(true); setError('')
    try {const updated = await api<User>('/auth/tutorial', {method:'PUT', body:JSON.stringify({choice})}); setUser(updated)}
    catch(e) {setError((e as Error).message)} finally {setBusy(false)}
  }
  return <div className="tutorial-backdrop"><section className="tutorial-modal" role="dialog" aria-modal="true" aria-labelledby="tutorial-title">
    {user.tutorial_choice === null ? <><p className="eyebrow">ПЕРВЫЙ ВХОД / ПУТЕВОДИТЕЛЬ</p><div className="tutorial-art"><span>01</span><span>02</span><span>03</span></div><h2 id="tutorial-title">Перед тобой целый остров</h2><p>Покажем за минуту, как решения меняют его. Можно сразу перейти к игре.</p>
      <div className="tutorial-actions"><button className="primary" disabled={busy} onClick={() => save('guide')}>Начать с инструкцией</button><button className="secondary" disabled={busy} onClick={() => save('skip')}>Начать без инструкции</button></div></>
    : <><p className="eyebrow">ПУТЕВОДИТЕЛЬ / {tutorialSteps[step].number} ИЗ 05</p><div className="tutorial-progress">{tutorialSteps.map((_,i) => <i className={i <= step ? 'done' : ''} key={i}/>)}</div><h2 id="tutorial-title">{tutorialSteps[step].title}</h2><p>{tutorialSteps[step].text}</p>
      <div className="tutorial-actions"><button className="primary" disabled={busy} onClick={() => step === tutorialSteps.length-1 ? save('complete') : setStep(step+1)}>{step === tutorialSteps.length-1 ? 'Начать игру' : 'Дальше'} <span>→</span></button><button className="text-button" disabled={busy} onClick={() => save('skip')}>Пропустить инструкцию</button></div></>}
    <ErrorBox message={error}/></section></div>
}

function Protected({children}: {children: ReactNode}) {const user = useApp(s => s.user); return user ? <>{children}</> : <Navigate to="/auth" replace/>}

export function App() {
  const user = useApp(s => s.user); const setUser = useApp(s => s.setUser); const [ready, setReady] = useState(false)
  const [sessionExpired, setSessionExpired] = useState(false)
  useEffect(() => {if (!localStorage.getItem('island-token')) {setReady(true); return}
    api<User>('/auth/me').then(setUser).catch(() => {localStorage.removeItem('island-token'); setSessionExpired(true)}).finally(() => setReady(true))
  }, [setUser])
  if (!ready) return <div className="loading">Загружаем остров…</div>
  return <><Routes><Route path="/auth" element={user ? <Navigate to={user.has_budget ? '/island' : '/onboarding'} replace/> : <Auth sessionExpired={sessionExpired}/>}/>
    <Route path="/onboarding" element={<Protected><Onboarding/></Protected>}/>
    <Route path="/island" element={<Protected>{user?.has_budget ? <IslandPage/> : <Navigate to="/onboarding"/>}</Protected>}/>
    <Route path="/history" element={<Protected><HistoryPage/></Protected>}/>
    <Route path="/scenario" element={<Protected><ScenarioPage/></Protected>}/>
    <Route path="/friends" element={<Protected><FriendsPage/></Protected>}/>
    <Route path="/profile" element={<Protected><ProfilePage/></Protected>}/>
    <Route path="*" element={<Navigate to={user ? user.has_budget ? '/island' : '/onboarding' : '/auth'} replace/>}/></Routes><Tutorial key={user?.id ?? 'anon'}/></>
}
