import csv
import random
from typing import Dict, List

from django.core.exceptions import ValidationError
from django.core.management.base import CommandError
from django.core.validators import validate_email

from phishing.management.commands._base import EmailCommand
from phishing.models import Target, TargetPool
from phishstick.settings import PHISHING_TEMPLATES


class Command(EmailCommand):
    help = 'Send emails to targets.'

    def add_arguments(self, parser):
        parser.add_argument('targets',
            help='A CSV file with two columns: email address and group.',
            type=lambda path: csv.reader(open(path, 'r', newline='')))
        parser.add_argument('--ignore-duplicates',
            help='Ignore duplicate addresses.',
            action='store_true')

    def handle(self, *args, **options):
        self.check_database()
        groups = self.get_groups(options['targets'], options['ignore_duplicates'])
        templates = self.get_templates()
        self.send_emails(groups, templates)

    def check_database(self):
        if Target.objects.exists() or TargetPool.objects.exists():
            self.stdout.write(self.style.WARNING(
                'The database is not empty! '
                'Please make sure that you know what you are doing!'))
            self.abort_if_no('Do you still want to continue? [y/n] ')

    def get_groups(self, targets: csv.reader, ignore_duplicates: bool) -> Dict[str, List[str]]:
        groups = {}
        addresses = set()
        for cols in targets:
            try:
                address, group = cols
                validate_email(address)
            except ValueError:
                self.abort(f'Wrong number of columns: {cols}.')
            except ValidationError:
                self.abort(f'Invalid email address: {address!r}.')

            groups.setdefault(group, []).append(address)
            if not ignore_duplicates and address in addresses:
                self.stdout.writelines([
                    self.style.ERROR(f'Email address present twice: {address!r}.'),
                    self.style.WARNING('Use \'--ignore-duplicates\' if this is desired.')])
                self.abort()
            else:
                addresses.add(address)

        for group in groups.values():
            random.shuffle(group)

        self.stdout.write(
            f'Found {len(addresses)} distinct email addresses.\n'
            f'Found {len(groups)} groups:')
        self.stdout.writelines(
            f' * {name!r} ({len(group)} addresses)' for name, group in groups.items())
        self.abort_if_no('Is this correct? [y/n] ')

        return groups

    def get_templates(self) -> List[str]:
        templates = list(PHISHING_TEMPLATES)
        self.stdout.write(f'Found {len(templates)} templates:')
        self.stdout.writelines(f' * {template!r}' for template in templates)
        self.abort_if_no('Is this correct? [y/n] ')
        return templates

    def send_emails(self, groups: Dict[str, List[str]], templates: List[str]):
        n_targets = sum(len(group) for group in groups.values())
        self.abort_if_no(f'Are you sure you want to send {n_targets} emails? [y/n] ')
        self.stdout.write(self.style.SUCCESS('Let the phishing begin!'))

        i = 0
        failures = []
        for group, addresses in groups.items():
            for template_i, template in enumerate(templates):
                pool, _ = TargetPool.objects.get_or_create(group=group, template=template)

                for address in addresses[template_i::len(templates)]:
                    target = Target.objects.create()

                    self.stdout.write(f'[{i+1}/{n_targets}]', ending=' ')
                    try:
                        self.send_email(address, target, pool)
                    except Exception as exc:
                        self.stdout.write(self.style.ERROR(f'Failed: {exc!r}'))
                        failures.append((address, target.id, pool.id))

                    i += 1

        self.save_failures(failures)
