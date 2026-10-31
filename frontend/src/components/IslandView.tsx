import type {Island} from '../lib/api'

export function IslandView({island}: {island: Island}) {
  const rainy = island.health_index < 45
  const bright = island.health_index >= 70
  return <div className="island-scene" role="img"
    aria-label={`Остров уровня ${island.level}. Погода: ${island.weather}. ${island.pollution}. Открыто деталей сбережений: ${island.savings_stage}.`}>
    <svg viewBox="0 0 620 360" preserveAspectRatio="xMidYMid meet" aria-hidden="true">
      <defs>
        <pattern id="map-grid" width="38" height="38" patternUnits="userSpaceOnUse"><path d="M38 0H0V38" fill="none" stroke="#a3c8bf" strokeWidth=".7" opacity=".28"/></pattern>
        <pattern id="map-dots" width="12" height="12" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r=".8" fill="#d2d2aa" opacity=".5"/></pattern>
      </defs>
      <rect width="620" height="360" fill={rainy ? '#456b72' : '#1e6973'}/>
      <rect width="620" height="360" fill="url(#map-grid)"/>
      <g fill="none" stroke="#b0d0c5" strokeWidth="1.2" opacity=".6">
        <path d="M36 81q16-8 32 0t32 0 M470 292q16-8 32 0t32 0 M515 184q16-8 32 0t32 0 M50 294q16-8 32 0t32 0"/>
        <path d="M110 42q16-8 32 0t32 0 M438 71q16-8 32 0t32 0 M375 320q16-8 32 0t32 0"/>
      </g>
      <g className="map-compass" transform="translate(560 55)" fill="none" stroke="#e7ddbb" strokeWidth="1.4"><circle r="25"/><path d="M0-35V35M-35 0H35M0-23L5 0 0 23-5 0Z" fill="#d6a36f"/><text x="-4" y="-40" fill="#e7ddbb" stroke="none" fontSize="10" fontFamily="Arial">N</text></g>
      <text x="32" y="35" fill="#d2e4d6" fontSize="10" fontFamily="Arial" letterSpacing="3">КАРТА СОСТОЯНИЯ / {String(island.level).padStart(2,'0')}</text>
      <path d="M76 219 Q112 183 174 185 Q213 140 276 148 Q342 119 404 155 Q491 165 536 210 Q561 248 518 273 Q455 301 375 286 Q306 312 222 290 Q138 299 93 269 Q55 250 76 219Z" fill="#d7b97e" stroke="#172f37" strokeWidth="5"/>
      <path d="M88 215 Q128 190 184 194 Q229 150 281 158 Q344 131 404 165 Q478 169 521 213 Q542 246 507 262 Q447 289 374 276 Q306 299 225 279 Q151 288 102 261 Q72 245 88 215Z" fill="#efe2bd" stroke="#172f37" strokeWidth="2"/>
      <path d="M107 221 Q158 200 204 208 Q243 168 294 171 Q344 148 392 176 Q468 183 501 219 Q502 241 473 251 Q425 268 375 257 Q302 281 234 260 Q160 272 117 248Z" fill={bright ? '#78a987' : rainy ? '#8b9c82' : '#a3b98c'} stroke="#315c55" strokeWidth="2"/>
      <path d="M126 240 Q201 224 278 236 T474 232" fill="none" stroke="#e7d7aa" strokeWidth="5" strokeDasharray="2 6"/>
      <path d="M157 215 Q210 188 270 204 M354 196 Q398 179 447 206" fill="none" stroke="#416d5e" strokeWidth="1.4" opacity=".55"/>
      <path d="M159 221 Q214 195 272 210 M356 204 Q401 187 447 214" fill="none" stroke="#416d5e" strokeWidth="1" opacity=".4"/>
      <rect x="88" y="158" width="45" height="18" fill="#efe2bd" stroke="#172f37" strokeWidth="1.5"/>
      <text x="94" y="171" fill="#172f37" fontSize="10" fontFamily="Arial">ПРИЧАЛ</text>
      {island.level >= 1 && <g className="building" transform="translate(101 227)"><path d="M0 25H55M12 25V3M12 3L47 14H12" stroke="#172f37" strokeWidth="3" fill="#dc7857"/><path d="M0 25V35M55 25V35" stroke="#172f37" strokeWidth="3"/></g>}
      {island.level >= 2 && <g className="building" transform="translate(264 185)"><path d="M0 26L36 0 72 26" fill="#d77856" stroke="#172f37" strokeWidth="3"/><rect x="8" y="26" width="56" height="48" fill="#f8eccb" stroke="#172f37" strokeWidth="3"/><rect x="28" y="46" width="16" height="28" fill="#457578" stroke="#172f37" strokeWidth="2"/><path d="M14 39h11m22 0h11" stroke="#172f37" strokeWidth="3"/></g>}
      {island.level >= 3 && <g className="building" transform="translate(393 187)"><path d="M0 18L27 0 54 18" fill="#d77856" stroke="#172f37" strokeWidth="3"/><rect x="5" y="18" width="44" height="49" fill="#e1cfa5" stroke="#172f37" strokeWidth="3"/><path d="M16 30h22M16 40h22M22 67V51h10v16" stroke="#172f37" strokeWidth="2"/></g>}
      {island.level >= 4 && <g className="building" transform="translate(201 187)"><path d="M16 51V23" stroke="#172f37" strokeWidth="5"/><circle cx="16" cy="16" r="19" fill="#4f8972" stroke="#172f37" strokeWidth="3"/><circle cx="37" cy="24" r="14" fill="#6a9d78" stroke="#172f37" strokeWidth="2"/><path d="M50 55V34" stroke="#172f37" strokeWidth="3"/></g>}
      {island.level >= 5 && <g className="building" transform="translate(348 141)"><path d="M0 14L25 0 50 14" fill="#d6a36f" stroke="#172f37" strokeWidth="3"/><rect x="4" y="14" width="42" height="75" fill="#e9dfba" stroke="#172f37" strokeWidth="3"/><path d="M13 27h24M13 42h24M13 57h24M20 89V72h10v17" stroke="#172f37" strokeWidth="2"/></g>}
      {island.savings_stage >= 1 && <g className="building" transform="translate(344 243)"><path d="M0 0h45v16H0Z" fill="#d2a777" stroke="#17363d" strokeWidth="2"/><path d="M7 11V2m10 9V2m10 9V2m10 9V2" stroke="#4c866c" strokeWidth="3"/><circle cx="7" cy="2" r="3" fill="#d77755"/><circle cx="27" cy="2" r="3" fill="#e2c47c"/></g>}
      {island.savings_stage >= 2 && <g className="building" transform="translate(139 196)"><path d="M0 34L10 8h28l10 26Z" fill="#b8d7c6" stroke="#17363d" strokeWidth="2"/><path d="M0 34h48v11H0Z" fill="#e6dbc0" stroke="#17363d" strokeWidth="2"/><path d="M10 8l9 26m19-26-9 26M24 8v37" stroke="#5c978e" strokeWidth="2"/></g>}
      {island.savings_stage >= 3 && <g className="building" transform="translate(474 177)"><path d="M8 60L14 12h21l6 48Z" fill="#f4e5c0" stroke="#17363d" strokeWidth="3"/><path d="M11 36h27M13 23h23" stroke="#d77755" strokeWidth="5"/><path d="M10 12h30l-5-8H15Z" fill="#d77755" stroke="#17363d" strokeWidth="2"/><circle cx="25" cy="-2" r="4" fill="#f8d995"/></g>}
      {island.cleanliness < 65 && <g className="pollution" fill="#5c625a" stroke="#172f37" strokeWidth="1"><path d="M467 251l12 1-3 7-11-2Z M490 263l8-2 3 7-9 2Z"/></g>}
      {rainy ? <g stroke="#c5d6d0" strokeWidth="2" opacity=".75"><path d="M123 89l-7 16m32 0-7 16m330-21-7 16m36 9-7 16"/></g> : <g className="sun" transform="translate(457 91)" stroke="#f1d3a0" fill="none" strokeWidth="2"><circle r="20" fill="#e6aa6d"/><path d="M0-32V-39M0 32V39M-32 0h-7M32 0h7M-23-23l-5-5M23 23l5 5"/></g>}
      <text x="34" y="333" fill="#d2e4d6" fontSize="10" fontFamily="Arial" letterSpacing="2">BERLOGATEAM / ОСТРОВ ДЕНЕГ</text>
      <text x="494" y="333" fill="#d2e4d6" fontSize="10" fontFamily="Arial" letterSpacing="2">0{island.level} / 05</text>
    </svg>
    <span className="island-level">УРОВЕНЬ {island.level} <i/> {island.weather}</span>
  </div>
}
