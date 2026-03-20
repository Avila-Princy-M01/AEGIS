"""Grow Vault — PyVax Smart Contract

Auto-compounding savings vault that collects Uniswap LP fees
and reinvests them. The Grow Agent deposits compounded fees
here, and a portion is swept into long-term savings.

Compiled via PyVax: Python → EVM bytecode.
"""

from pyvax import contract, uint256, address, mapping, event, require, msg, block


@contract
class GrowVault:
    """Auto-compounding savings vault for LP fee management."""

    # State variables
    owner: address
    grow_agent: address
    total_savings: uint256
    total_compounded: uint256
    compound_count: uint256
    last_compound_time: uint256
    savings: mapping[address, uint256]

    # Events
    FeeCompounded: event({"amount": uint256, "total": uint256, "count": uint256})
    SavingsDeposited: event({"from_agent": address, "amount": uint256})
    SavingsWithdrawn: event({"to": address, "amount": uint256})

    def __init__(self, _grow_agent: address):
        """Deploy with the Grow Agent's address."""
        self.owner = msg.sender
        self.grow_agent = _grow_agent
        self.total_savings = 0
        self.total_compounded = 0
        self.compound_count = 0
        self.last_compound_time = block.timestamp

    def deposit_compound(self):
        """Grow Agent deposits compounded fees."""
        require(
            msg.sender == self.grow_agent or msg.sender == self.owner,
            "Only grow agent or owner",
        )
        require(msg.value > 0, "Must deposit > 0")

        self.savings[self.owner] += msg.value
        self.total_savings += msg.value
        self.total_compounded += msg.value
        self.compound_count += 1
        self.last_compound_time = block.timestamp

        self.FeeCompounded(msg.value, self.total_compounded, self.compound_count)
        self.SavingsDeposited(msg.sender, msg.value)

    def withdraw_savings(self, amount: uint256):
        """Owner withdraws from savings."""
        require(msg.sender == self.owner, "Only owner")
        require(self.savings[self.owner] >= amount, "Insufficient savings")

        self.savings[self.owner] -= amount
        self.total_savings -= amount
        self.owner.transfer(amount)
        self.SavingsWithdrawn(self.owner, amount)

    def get_savings(self) -> uint256:
        """View: total savings for the owner."""
        return self.savings[self.owner]

    def get_stats(self) -> (uint256, uint256, uint256):
        """View: total savings, total compounded, compound count."""
        return (self.total_savings, self.total_compounded, self.compound_count)
