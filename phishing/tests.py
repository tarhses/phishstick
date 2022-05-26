from datetime import datetime

from django.test import TestCase
from django.utils.timezone import make_aware

from phishing.models import Status, Target, TargetPool


class TargetTestCase(TestCase):
    def test_upgrade_status_to_sent(self):
        t = Target.objects.create()

        sent_at = make_aware(datetime(2053, 12, 25, 14, 12, 29))
        statuses = t.upgrade_status(Status.SENT, at=sent_at)

        self.assertSetEqual(statuses, {Status.SENT})
        self.assertEqual(t.sent_at, sent_at)
        self.assertEqual(t.opened_at, None)
        self.assertEqual(t.clicked_at, None)
        self.assertEqual(t.phished_at, None)

    def test_upgrade_status_to_opened(self):
        sent_at = make_aware(datetime(2022, 6, 4, 8, 32, 15))
        t = Target.objects.create(sent_at=sent_at)

        opened_at = make_aware(datetime(2022, 6, 5, 12, 30, 45))
        statuses = t.upgrade_status(Status.OPENED, at=opened_at)

        self.assertSetEqual(statuses, {Status.OPENED})
        self.assertEqual(t.sent_at, sent_at)
        self.assertEqual(t.opened_at, opened_at)
        self.assertEqual(t.clicked_at, None)
        self.assertEqual(t.phished_at, None)

    def test_upgrade_status_to_clicked(self):
        sent_at = make_aware(datetime(2023, 2, 10, 12, 0, 46))
        t = Target.objects.create(sent_at=sent_at)

        clicked_at = make_aware(datetime(2023, 2, 10, 12, 12, 2))
        statuses = t.upgrade_status(Status.CLICKED, at=clicked_at)

        self.assertSetEqual(statuses, {Status.OPENED, Status.CLICKED})
        self.assertEqual(t.sent_at, sent_at)
        self.assertEqual(t.opened_at, clicked_at)
        self.assertEqual(t.clicked_at, clicked_at)
        self.assertEqual(t.phished_at, None)

    def test_upgrade_status_to_phished(self):
        sent_at = make_aware(datetime(2010, 4, 5, 5, 5, 17))
        t = Target.objects.create(sent_at=sent_at)

        phished_at = make_aware(datetime(2010, 4, 5, 14, 2, 54))
        statuses = t.upgrade_status(Status.PHISHED, at=phished_at)

        self.assertSetEqual(statuses, {Status.OPENED, Status.CLICKED, Status.PHISHED})
        self.assertEqual(t.sent_at, sent_at)
        self.assertEqual(t.opened_at, phished_at)
        self.assertEqual(t.clicked_at, phished_at)
        self.assertEqual(t.phished_at, phished_at)

    def test_upgrade_status_to_opened_then_phished(self):
        sent_at = make_aware(datetime(2020, 7, 27, 7, 0, 3))
        t = Target.objects.create(sent_at=sent_at)

        opened_at = make_aware(datetime(2020, 7, 28, 10, 28, 22))
        statuses1 = t.upgrade_status(Status.OPENED, at=opened_at)
        phished_at = make_aware(datetime(2022, 7, 28, 10, 30, 7))
        statuses2 = t.upgrade_status(Status.PHISHED, at=phished_at)

        self.assertSetEqual(statuses1, {Status.OPENED})
        self.assertSetEqual(statuses2, {Status.CLICKED, Status.PHISHED})
        self.assertEqual(t.sent_at, sent_at)
        self.assertEqual(t.opened_at, opened_at)
        self.assertEqual(t.clicked_at, phished_at)
        self.assertEqual(t.phished_at, phished_at)

    def test_downgrade_status_to_opened(self):
        sent_at = make_aware(datetime(2023, 1, 3, 16, 45, 4))
        phished_at = make_aware(datetime(2023, 1, 4, 10, 23, 12))
        t = Target.objects.create(
            sent_at=sent_at, opened_at=phished_at, clicked_at=phished_at, phished_at=phished_at)

        opened_at = make_aware(datetime(2023, 1, 4, 10, 25, 48))
        statuses = t.upgrade_status(Status.OPENED)

        self.assertSetEqual(statuses, set())
        self.assertEqual(t.sent_at, sent_at)
        self.assertEqual(t.opened_at, phished_at)
        self.assertEqual(t.clicked_at, phished_at)
        self.assertEqual(t.phished_at, phished_at)


class TargetPoolTestCase(TestCase):
    def test_increment_sent_status(self):
        p = TargetPool.objects.create(group='accounting', template='weird')

        p.increment_statuses({Status.SENT})
        p.refresh_from_db()

        self.assertEqual(p.sent_count, 1)
        self.assertEqual(p.opened_count, 0)
        self.assertEqual(p.clicked_count, 0)
        self.assertEqual(p.phished_count, 0)

    def test_increment_opened_status(self):
        p = TargetPool.objects.create(group='marketing', template='aggressive')

        p.increment_statuses({Status.OPENED})
        p.refresh_from_db()

        self.assertEqual(p.sent_count, 0)
        self.assertEqual(p.opened_count, 1)
        self.assertEqual(p.clicked_count, 0)
        self.assertEqual(p.phished_count, 0)

    def test_increment_clicked_status(self):
        p = TargetPool.objects.create(group='training', template='illogical')

        p.increment_statuses({Status.CLICKED})
        p.refresh_from_db()

        self.assertEqual(p.sent_count, 0)
        self.assertEqual(p.opened_count, 0)
        self.assertEqual(p.clicked_count, 1)
        self.assertEqual(p.phished_count, 0)

    def test_increment_phished_status(self):
        p = TargetPool.objects.create(group='management', template='cheap')

        p.increment_statuses({Status.PHISHED})
        p.refresh_from_db()

        self.assertEqual(p.sent_count, 0)
        self.assertEqual(p.opened_count, 0)
        self.assertEqual(p.clicked_count, 0)
        self.assertEqual(p.phished_count, 1)

    def test_increment_sent_opened_clicked_statuses(self):
        p = TargetPool.objects.create(group='r&d', template='weird')

        p.increment_statuses({Status.SENT, Status.OPENED, Status.CLICKED})
        p.refresh_from_db()

        self.assertEqual(p.sent_count, 1)
        self.assertEqual(p.opened_count, 1)
        self.assertEqual(p.clicked_count, 1)
        self.assertEqual(p.phished_count, 0)
