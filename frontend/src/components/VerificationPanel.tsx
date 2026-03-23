interface TxProof {
  label: string
  chain: string
  hash: string
  url: string
  type: 'identity' | 'swap'
}

const PROOFS: TxProof[] = [
  {
    label: 'ERC-8004 Agent Identity',
    chain: 'Base Mainnet',
    hash: '0x48a190093bad8a57c0e4c4feba3a783f7c2f63625aad4e978db62fce9c625389',
    url: 'https://basescan.org/tx/0x48a190093bad8a57c0e4c4feba3a783f7c2f63625aad4e978db62fce9c625389',
    type: 'identity',
  },
  {
    label: 'Uniswap Swap #1',
    chain: 'Sepolia Testnet',
    hash: '0x83087cd184dd637b85594e10928e2cc9e255cd847c2875e1275c57d1f79591fe',
    url: 'https://sepolia.etherscan.io/tx/0x83087cd184dd637b85594e10928e2cc9e255cd847c2875e1275c57d1f79591fe',
    type: 'swap',
  },
  {
    label: 'Uniswap Swap #2',
    chain: 'Sepolia Testnet',
    hash: '0xdc3ab4f3e67ce95fda153bcba84454dfcbf782cd20bbcfd73a14946650621acb',
    url: 'https://sepolia.etherscan.io/tx/0xdc3ab4f3e67ce95fda153bcba84454dfcbf782cd20bbcfd73a14946650621acb',
    type: 'swap',
  },
]

const AGENT_WALLET = '0x9aC234De759456f2b65FB7C182CFCE013889390A'

function shortenHash(hash: string): string {
  return `${hash.slice(0, 10)}…${hash.slice(-8)}`
}

export function VerificationPanel() {
  return (
    <div className="verification-panel-wrapper">
      <div className="panel verification-panel">
        <div className="panel-header">
          <div
            className="panel-icon"
            style={{ background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.25), rgba(59, 130, 246, 0.15))' }}
          >
            ✅
          </div>
          <div>
            <h2>On-Chain Verification</h2>
            <span className="panel-label">Cryptographic proof of all agent actions</span>
          </div>
          <div className="verified-badge">
            <span className="verified-badge-dot" />
            Verified On-Chain
          </div>
        </div>

        <div className="verification-grid">
          {PROOFS.map((proof) => (
            <a
              key={proof.hash}
              href={proof.url}
              target="_blank"
              rel="noopener noreferrer"
              className={`verification-card verification-card--${proof.type}`}
            >
              <div className="verification-card__icon">
                {proof.type === 'identity' ? '🪪' : '🦄'}
              </div>
              <div className="verification-card__info">
                <span className="verification-card__label">{proof.label}</span>
                <span className="verification-card__chain">{proof.chain}</span>
                <span className="verification-card__hash">{shortenHash(proof.hash)}</span>
              </div>
              <span className="verification-card__arrow">↗</span>
            </a>
          ))}

          <div className="verification-card verification-card--wallet">
            <div className="verification-card__icon">🔑</div>
            <div className="verification-card__info">
              <span className="verification-card__label">Agent Wallet</span>
              <span className="verification-card__chain">Self-Custody</span>
              <span className="verification-card__hash">{shortenHash(AGENT_WALLET)}</span>
            </div>
          </div>
        </div>

        <div className="verification-footer">
          <span className="verification-footer__icon">🔒</span>
          <span>All actions logged on-chain via ERC-8004 · Read-only monitoring · No private keys required</span>
        </div>
      </div>
    </div>
  )
}
