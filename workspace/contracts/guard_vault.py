"""Guard Vault — PyVax Smart Contract

A threat-response vault that receives LP tokens or native tokens
when Guard Agent detects a threat. Funds are locked until the
threat is cleared or the owner manually withdraws.

Compiled via PyVax: Python → EVM bytecode.
"""

# PyVax contract definition
# This follows the PyVax Python→EVM syntax

from pyvax import contract, uint256, address, mapping, event, require, msg


@contract
class GuardVault:
    """Emergency vault that locks funds during detected threats."""

    # State variables
    owner: address
    guardian: address  # The Guard Agent's wallet address
    is_locked: bool
    total_deposited: uint256
    balances: mapping[address, uint256]

    # Events
    Deposited: event({"sender": address, "amount": uint256})
    Withdrawn: event({"to": address, "amount": uint256})
    VaultLocked: event({"by": address, "reason": str})
    VaultUnlocked: event({"by": address})

    def __init__(self, _guardian: address):
        """Deploy with the Guard Agent's address as authorized guardian."""
        self.owner = msg.sender
        self.guardian = _guardian
        self.is_locked = False
        self.total_deposited = 0

    def deposit(self):
        """Deposit native tokens into the vault."""
        require(msg.value > 0, "Must deposit > 0")
        self.balances[msg.sender] += msg.value
        self.total_deposited += msg.value
        self.Deposited(msg.sender, msg.value)

    def lock(self, reason: str):
        """Lock the vault — only callable by the Guard Agent."""
        require(
            msg.sender == self.guardian or msg.sender == self.owner,
            "Only guardian or owner can lock",
        )
        self.is_locked = True
        self.VaultLocked(msg.sender, reason)

    def unlock(self):
        """Unlock the vault — only callable by the Guard Agent or owner."""
        require(
            msg.sender == self.guardian or msg.sender == self.owner,
            "Only guardian or owner can unlock",
        )
        self.is_locked = False
        self.VaultUnlocked(msg.sender)

    def withdraw(self, amount: uint256):
        """Withdraw funds — blocked while vault is locked."""
        require(not self.is_locked, "Vault is locked — threat active")
        require(self.balances[msg.sender] >= amount, "Insufficient balance")
        self.balances[msg.sender] -= amount
        self.total_deposited -= amount
        # Transfer native tokens back to sender
        msg.sender.transfer(amount)
        self.Withdrawn(msg.sender, amount)

    def emergency_withdraw(self):
        """Owner-only emergency withdrawal — bypasses lock."""
        require(msg.sender == self.owner, "Only owner")
        amount = self.balances[self.owner]
        require(amount > 0, "No balance")
        self.balances[self.owner] = 0
        self.total_deposited -= amount
        self.owner.transfer(amount)
        self.Withdrawn(self.owner, amount)

    def get_balance(self, user: address) -> uint256:
        """View: check a user's deposited balance."""
        return self.balances[user]

    def get_status(self) -> (bool, uint256):
        """View: return lock status and total deposits."""
        return (self.is_locked, self.total_deposited)
