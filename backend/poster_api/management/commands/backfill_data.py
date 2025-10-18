import logging
from datetime import datetime
from django.core.management.base import BaseCommand


from poster_api.services.saving import sync_all_from_date, PosterAPIClient
from poster_api.services.saving import create_role_lists 


logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Runs a full historical data sync from a specified start date."

    def add_arguments(self, parser):
        parser.add_argument(
            '--start_date',
            type=str,
            required=True,
            help='Start date for historical sync (YYYY-MM-DD).'
        )
        parser.add_argument(
            '--spot_id',
            type=int,
            default=1,
            help='Specify the spot_id for the sync.'
        )

    def handle(self, *args, **options):
        start_date = options['start_date']
        spot_id = options['spot_id']
        api_client = PosterAPIClient()

        try:
            datetime.strptime(start_date, '%Y-%m-%d')
        except ValueError:
            self.stderr.write(self.style.ERROR("Invalid date format. Use YYYY-MM-DD."))
            return

        self.stdout.write(self.style.SUCCESS(f"=== Starting FULL historical sync ==="))
        self.stdout.write(f"Start Date: {start_date}")
        self.stdout.write(f"Spot ID: {spot_id}")
        
        self.stdout.write("Step 1: Ensuring roles exist...")
        create_role_lists(api_client)
        self.stdout.write(self.style.SUCCESS("Roles ensured."))

        self.stdout.write(f"Step 2: Starting sync_all_from_date...")
        self.stdout.write(self.style.WARNING(
            "This will take a long time. Do not interrupt."
        ))
        
        try:
            sync_all_from_date(api_client, start_date, spot_id)
            self.stdout.write(self.style.SUCCESS(
                "=== FULL historical sync complete! ==="
            ))
        except Exception as e:
            logger.error(f"FATAL error during backfill: {e}", exc_info=True)
            self.stderr.write(self.style.ERROR(f"FATAL error during backfill: {e}"))
            self.stderr.write(self.style.ERROR("Check logs. Data may be incomplete."))