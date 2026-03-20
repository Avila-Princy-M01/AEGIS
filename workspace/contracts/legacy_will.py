"""Legacy Will — PyVax Smart Contract

Trustless digital will with dead man's switch. The owner deposits
assets and designates beneficiaries with percentage shares. If the
owner doesn't check in within the inactivity threshold, anyone
can trigger the distribution to beneficiaries.

Compiled via PyVax: Python → EVM bytecode.
"""

from pyvax import contract, uint256, address, mapping, event, require, msg, block


@contract
class LegacyWill:
    """Digital will with dead man's switch for crypto inheritance."""

    # State variables
    owner: address
    legacy_agent: address
    last_check_in: uint256
    inactivity_threshold: uint256  # in seconds
    is_distributed: bool
    total_balance: uint256

    # Beneficiary storage (up to 10)
    beneficiary_count: uint256
    beneficiary_addresses: mapping[uint256, address]
    beneficiary_shares: mapping[uint256, uint256]  # basis points (10000 = 100%)

    # Events
    CheckedIn: event({"owner": address, "timestamp": uint256})
    BeneficiaryAdded: event({"addr": address, "share_bps": uint256})
    InheritanceTriggered: event({"triggered_by": address, "timestamp": uint256})
    Distributed: event({"beneficiary": address, "amount": uint256})
    Deposited: event({"from": address, "amount": uint256})

    def __init__(self, _legacy_agent: address, _threshold_seconds: uint256):
        """Deploy with agent address and inactivity threshold."""
        self.owner = msg.sender
        self.legacy_agent = _legacy_agent
        self.last_check_in = block.timestamp
        self.inactivity_threshold = _threshold_seconds
        self.is_distributed = False
        self.total_balance = 0
        self.beneficiary_count = 0

    def deposit(self):
        """Deposit native tokens into the will."""
        require(msg.value > 0, "Must deposit > 0")
        self.total_balance += msg.value
        self.Deposited(msg.sender, msg.value)

    def check_in(self):
        """Owner checks in — resets the inactivity timer."""
        require(msg.sender == self.owner, "Only owner can check in")
        require(not self.is_distributed, "Already distributed")
        self.last_check_in = block.timestamp
        self.CheckedIn(self.owner, block.timestamp)

    def add_beneficiary(self, _addr: address, _share_bps: uint256):
        """Add a beneficiary with their share in basis points."""
        require(msg.sender == self.owner, "Only owner")
        require(self.beneficiary_count < 10, "Max 10 beneficiaries")
        require(_share_bps > 0 and _share_bps <= 10000, "Invalid share")

        idx = self.beneficiary_count
        self.beneficiary_addresses[idx] = _addr
        self.beneficiary_shares[idx] = _share_bps
        self.beneficiary_count += 1
        self.BeneficiaryAdded(_addr, _share_bps)

    def trigger_distribution(self):
        """Trigger inheritance — callable by anyone after threshold."""
        require(not self.is_distributed, "Already distributed")
        require(
            block.timestamp >= self.last_check_in + self.inactivity_threshold,
            "Inactivity threshold not reached",
        )

        self.is_distributed = True
        self.InheritanceTriggered(msg.sender, block.timestamp)

        balance = self.total_balance
        i = 0
        while i < self.beneficiary_count:
            addr = self.beneficiary_addresses[i]
            share = self.beneficiary_shares[i]
            amount = balance * share / 10000
            if amount > 0:
                addr.transfer(amount)
                self.Distributed(addr, amount)
            i += 1

        self.total_balance = 0

    def get_time_remaining(self) -> uint256:
        """View: seconds until inheritance can be triggered."""
        deadline = self.last_check_in + self.inactivity_threshold
        if block.timestamp >= deadline:
            return 0
        return deadline - block.timestamp

    def withdraw(self, amount: uint256):
        """Owner withdraws before distribution."""
        require(msg.sender == self.owner, "Only owner")
        require(not self.is_distributed, "Already distributed")
        require(amount <= self.total_balance, "Insufficient balance")
        self.total_balance -= amount
        self.owner.transfer(amount)
