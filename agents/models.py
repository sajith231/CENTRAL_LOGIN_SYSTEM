import secrets

from django.db import models
from django.db.models.functions import Lower

# Ambiguous characters (0/O, 1/I) are left out so referral codes stay readable
REFERRAL_ALPHABET = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
REFERRAL_PREFIX = 'AG-'


def generate_unique_referral_code():
    """Build a referral code that no other agent is using yet."""
    while True:
        code = REFERRAL_PREFIX + ''.join(secrets.choice(REFERRAL_ALPHABET) for _ in range(6))
        if not Agent.objects.filter(referral_code=code).exists():
            return code


class Agent(models.Model):
    name = models.CharField(max_length=150)
    code = models.CharField(
        max_length=50,
        unique=True,
        help_text='Manually typed, unique agent code.',
    )
    number = models.CharField(max_length=30)
    company_name = models.CharField(max_length=200)
    referral_code = models.CharField(
        max_length=30,
        unique=True,
        editable=False,
        help_text='Auto generated on create and never editable afterwards.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Agent'
        verbose_name_plural = 'Agents'
        constraints = [
            # A company may hold several agents, and the same agent name may
            # appear under different companies - but not twice in one company.
            models.UniqueConstraint(
                Lower('name'),
                Lower('company_name'),
                name='unique_agent_name_per_company',
                violation_error_message=(
                    'An agent with this name already exists for this company.'
                ),
            ),
        ]

    def __str__(self):
        return f'{self.name} ({self.code})'

    def save(self, *args, **kwargs):
        self.name = (self.name or '').strip()
        self.code = (self.code or '').strip()
        self.number = (self.number or '').strip()
        self.company_name = (self.company_name or '').strip()

        # Referral code is assigned once, on creation, and never regenerated
        if not self.referral_code:
            self.referral_code = generate_unique_referral_code()

        super().save(*args, **kwargs)


class AgentReferral(models.Model):
    """A mail id submitted through the public agent referral API."""

    agent = models.ForeignKey(
        Agent,
        on_delete=models.CASCADE,
        related_name='referrals',
    )
    mail_id = models.EmailField(max_length=254)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Agent Referral'
        verbose_name_plural = 'Agent Referrals'
        constraints = [
            # The same mail id should appear only once per agent
            models.UniqueConstraint(
                'agent',
                Lower('mail_id'),
                name='unique_mail_per_agent',
                violation_error_message=(
                    'This mail id is already registered for this agent.'
                ),
            ),
        ]

    def __str__(self):
        return f'{self.mail_id} -> {self.agent.referral_code}'

    def save(self, *args, **kwargs):
        self.mail_id = (self.mail_id or '').strip()
        super().save(*args, **kwargs)
