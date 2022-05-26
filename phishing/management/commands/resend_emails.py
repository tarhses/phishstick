import csv

from phishing.management.commands._base import EmailCommand
from phishing.models import Target, TargetPool


class Command(EmailCommand):
    help = 'Retry failed email attempts.'

    def add_arguments(self, parser):
        parser.add_argument('failures',
            help='A CSV file with three columns: email address, target ID, and pool ID.',
            type=lambda path: csv.reader(open(path, 'r', newline='')))

    def handle(self, *args, **options):
        rows = list(options['failures'])

        self.stdout.write(f'Found {len(rows)} failures.')
        self.abort_if_no('Are you sure you want to retry sending these emails? [y/n] ')

        failures = []
        for i, row in enumerate(rows):
            address, target_id, pool_id = row
            target = Target.objects.get(pk=target_id)
            pool = TargetPool.objects.get(pk=pool_id)

            self.stdout.write(f'[{i+1}/{len(rows)}]', ending=' ')
            try:
                self.send_email(address, target, pool)
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f'Failed: {exc!r}'))
                failures.append((address, target.id, pool.id))

        self.save_failures(failures)
