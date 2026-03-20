import { useState } from 'react'

interface Props {
  onDeploy: (command: string) => void
  deploying: boolean
}

const PLACEHOLDER = 'Protect my Uniswap positions, compound my fees, and if I disappear for 30 days, send everything to my family...'

const EXAMPLES = [
  'Protect my LP positions from crashes, grow them safely, and if I don\'t check in for 30 days, send them to 0xABC...',
  'Guard my Uniswap pools aggressively, auto-compound fees hourly, 90-day dead man\'s switch',
  'Conservative protection, weekly compounding, distribute to 3 wallets after 60 days inactive',
]

export function CommandInput({ onDeploy, deploying }: Props) {
  const [command, setCommand] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const cmd = command.trim() || PLACEHOLDER
    onDeploy(cmd)
  }

  return (
    <form className="command-input" onSubmit={handleSubmit}>
      <div className="input-wrapper">
        <textarea
          value={command}
          onChange={e => setCommand(e.target.value)}
          placeholder={PLACEHOLDER}
          rows={3}
          disabled={deploying}
        />
        <button type="submit" disabled={deploying} className="deploy-btn">
          {deploying ? (
            <span className="spinner" />
          ) : (
            '🚀 Deploy Agents'
          )}
        </button>
      </div>
      <div className="examples">
        <span className="examples-label">Try:</span>
        {EXAMPLES.map((ex, i) => (
          <button
            key={i}
            type="button"
            className="example-chip"
            onClick={() => setCommand(ex)}
          >
            {ex.slice(0, 50)}...
          </button>
        ))}
      </div>
    </form>
  )
}
