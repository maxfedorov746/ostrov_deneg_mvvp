export function Brand({large = false}: {large?: boolean}) {
  return <div className={`brand ${large ? 'brand-large' : ''}`} aria-label="Остров Денег">
    <span className="brand-symbol" aria-hidden="true"><i/><i/><i/></span>
    <span className="brand-name">ОСТРОВ<br/>ДЕНЕГ</span>
  </div>
}
