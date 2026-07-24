import csv
import os
from django.core.management.base import BaseCommand
from bikes.models import Bike

class Command(BaseCommand):
    help = 'Import bikes from CSV file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            default=os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'bikes.csv'),
            help='Path to CSV file',
        )

    def handle(self, *args, **options):
        path = options['file']
        if not os.path.exists(path):
            self.stderr.write(f'File not found: {path}')
            return

        Bike.objects.all().delete()
        created = 0
        errors  = 0

        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    Bike.objects.create(
                        bike_name          = row['bike_name'].strip(),
                        brand              = row['brand'].strip(),
                        year               = int(row['year']),
                        fuel_type          = row['fuel_type'].strip(),
                        kms_driven         = int(row['kms_driven']),
                        engine_capacity_cc = int(row['engine_capacity_cc']),
                        price_usd          = float(row['price_usd']),
                    )
                    created += 1
                except Exception as e:
                    errors += 1
                    self.stderr.write(f'Row error: {e} — {row}')

        self.stdout.write(self.style.SUCCESS(
            f'Import complete: {created} bikes added, {errors} errors.'
        ))
