import secrets
from datetime import datetime
from enum import IntEnum
from typing import Optional, Set

from django.db import transaction
from django.db.models import CharField, DateTimeField, F, IntegerField, Model, PositiveIntegerField
from django.utils.timezone import now


def generate_id():
    """Generate a cryptographically secure random ID."""

    # SECURITY WARNING: we must use the "secrets" module, as "random" is not a
    # cryptographically-secure pseudo-random number generator (CSPRNG)!
    return secrets.token_urlsafe(8)


class Status(IntEnum):
    """Current status of a target."""

    SENT = 1
    OPENED = 2
    CLICKED = 3
    PHISHED = 4


class Target(Model):
    """Anonymous target of a phishing campaign.

    Once the email is sent, the user's email address is discarded. We only
    store a randomly generated ID in the database. This ID is used to ensure
    that a given target won't be counted twice in the campaign results.
    """
    id = CharField(primary_key=True, max_length=32, default=generate_id)
    sent_at = DateTimeField(null=True, blank=True, default=None)
    opened_at = DateTimeField(null=True, blank=True, default=None)
    clicked_at = DateTimeField(null=True, blank=True, default=None)
    phished_at = DateTimeField(null=True, blank=True, default=None)

    # This method is atomic to avoid race conditions!
    @transaction.atomic
    def upgrade_status(self, new_status: Status, at: Optional[datetime] = None) -> Set[Status]:
        """Upgrade the current status to a higher one, and return a set
        containing all the statuses that were actually updated.

        The "at" parameter contains the timestamp at which the status has been
        upgraded. If it is None, current time is used.

        If a status is skipped, all intermediate statuses are also updated. For
        instance, if the status changes from "sent" to "phished", "clicked"
        will also be updated. In that case, the returned set will contain both
        "clicked" and "phished".
        """
        if at is None:
            at = now()

        new_statuses = set()
        if new_status >= Status.SENT and self.sent_at is None:
            self.sent_at = at
            new_statuses.add(Status.SENT)
        if new_status >= Status.OPENED and self.opened_at is None:
            self.opened_at = at
            new_statuses.add(Status.OPENED)
        if new_status >= Status.CLICKED and self.clicked_at is None:
            self.clicked_at = at
            new_statuses.add(Status.CLICKED)
        if new_status >= Status.PHISHED and self.phished_at is None:
            self.phished_at = at
            new_statuses.add(Status.PHISHED)

        self.save()
        return new_statuses


class TargetPool(Model):
    """Results of a phishing campaign for a given (group, template) tuple."""

    id = CharField(primary_key=True, max_length=32, default=generate_id)
    group = CharField(max_length=256)
    template = CharField(max_length=256)
    sent_count = PositiveIntegerField(default=0)
    opened_count = PositiveIntegerField(default=0)
    clicked_count = PositiveIntegerField(default=0)
    phished_count = PositiveIntegerField(default=0)

    def increment_statuses(self, statuses: Set[Status]):
        """Increment status counters for provided statuses."""

        # We use the "F" function to avoid race conditions.
        # See https://docs.djangoproject.com/en/4.0/ref/models/expressions/#avoiding-race-conditions-using-f-1
        if len(statuses) > 0:
            if Status.SENT in statuses:
                self.sent_count = F('sent_count') + 1
            if Status.OPENED in statuses:
                self.opened_count = F('opened_count') + 1
            if Status.CLICKED in statuses:
                self.clicked_count = F('clicked_count') + 1
            if Status.PHISHED in statuses:
                self.phished_count = F('phished_count') + 1
            self.save()
