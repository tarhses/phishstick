import csv
import random
from datetime import datetime
from typing import List, Optional, Tuple

from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError
from django.template.loader import render_to_string

from phishing.models import Status, Target, TargetPool
from phishstick.settings import DEBUG, PHISHING_TEMPLATES


class EmailCommand(BaseCommand):
    requires_migrations_checks = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if DEBUG:
            self.stdout.write(self.style.WARNING('Debug mode, no actual email will be sent!'))

    def send_email(self, address: str, target: Target, pool: TargetPool):
        self.stdout.write(
            f'Sending email to {address!r} '
            f'(group={pool.group!r}, template={pool.template!r}).')

        if DEBUG and random.random() < 0.1:
            # In debug mode, simulate a 10% chance to fail.
            raise Exception('bad luck')

        config = PHISHING_TEMPLATES[pool.template]
        context = {'target_id': target.id, 'pool_id': pool.id}
        text_message = render_to_string(config['TEXT_TEMPLATE'], context)
        html_message = render_to_string(config['HTML_TEMPLATE'], context)
        send_mail(
            subject=config['SUBJECT'],
            message=text_message,
            html_message=html_message,
            from_email=config['FROM'],
            recipient_list=[address],
            fail_silently=False)

        new_statuses = target.upgrade_status(Status.SENT)
        pool.increment_statuses(new_statuses)

    def save_failures(self, failures: List[Tuple[str, str, str]]):
        if len(failures) == 0:
            self.stdout.write(self.style.SUCCESS('Done. All emails sent.'))
        else:
            now = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
            path = f'failures.{now}.csv'
            self.stdout.writelines([
                self.style.ERROR(f'Done. However, {len(failures)} emails could not be sent.'),
                self.style.WARNING(f'Use \'python manage.py resend_emails {path}\' to retry.')])
            with open(path, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerows(failures)

    def abort(self, text: Optional[str] = None):
        if text is not None:
            self.stdout.write(self.style.ERROR(text))
        raise CommandError('Aborted.')

    def abort_if_yes(self, *args, **kwargs):
        if self.input_yes(*args, **kwargs):
            self.abort()

    def abort_if_no(self, *args, **kwargs):
        if self.input_no(*args, **kwargs):
            self.abort()

    def input_yes(self, *args, **kwargs) -> bool:
        response = ''
        while response != 'y' and response != 'n':
            response = input(*args, **kwargs).strip().lower()[:1]
        return response == 'y'

    def input_no(self, *args, **kwargs) -> bool:
        return not self.input_yes(*args, **kwargs)
