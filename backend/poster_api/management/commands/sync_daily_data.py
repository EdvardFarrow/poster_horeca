import logging
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.db import transaction


from poster_api.services.saving import (
    save_cash_shifts_range,
    save_products_sales,
    save_categories_sales,
    save_clients,
    save_transactions,
    save_transactions_products,
    save_transaction_history,
    save_shift_sales_to_db,
    save_workshop,
    save_payments_id,
    save_products,
    save_categories,
    PosterAPIClient
)
from salary.services import calculate_and_save_shift_salaries
from shift.models import Shift

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    """
    Everyday command for CRON
    1. Sync all data from Poster API for previous day 
    2. Calculate and save salaries for all shift for previous day 
    """
    help = "Runs the full daily data sync and salary calculation for the previous day."

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Run sync for a specific date (YYYY-MM-DD) instead of yesterday.'
        )
        parser.add_argument(
            '--skip-salary',
            action='store_true',
            help='Only sync data, do not calculate salaries.'
        )
        parser.add_argument(
            '--skip-static',
            action='store_true',
            help='Skip syncing static data (products, workshops, etc.).'
        )
        parser.add_argument(
            '--spot_id',
            type=int,
            default=1,
            help='Specify the spot_id for the sync.'
        )
        parser.add_argument(
            '--force-salary',
            action='store_true',
            help='Attempt salary calculation even if data sync fails.'
        )

    def handle(self, *args, **options):
        if options['date']:
            date_str = options['date']
            try:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                self.stderr.write(self.style.ERROR("Invalid date format. Use YYYY-MM-DD."))
                return
        else:
            date_obj = datetime.now().date() - timedelta(days=1)
            date_str = date_obj.strftime('%Y-%m-%d')
        
        spot_id = options['spot_id']
        api_client = PosterAPIClient()

        self.stdout.write(self.style.SUCCESS(f"=== Starting daily sync for {date_str} (Spot ID: {spot_id}) ==="))

        try:
            if not options['skip_static']:
                self.stdout.write("Syncing static data (workshops, payments, products)...")
                save_workshop(api_client.get_workshop())
                save_payments_id(api_client.get_payments_id())
                save_products(api_client.get_products())
                save_categories(api_client.get_category())
                self.stdout.write(self.style.SUCCESS("Static data synced."))
            else:
                self.stdout.write("Skipping static data sync.")

            self.stdout.write(f"Syncing transactional data for {date_str}...")
            
            with transaction.atomic():
                save_cash_shifts_range(api_client, date_str, spot_id, date_str)
                
                products_sales = api_client.get_products_sales(date_str, date_str, spot_id)
                save_products_sales(products_sales)

                categories_sales = api_client.get_categories_sales(date_str, date_str, spot_id)
                save_categories_sales(categories_sales)
                
                clients_sales = api_client.get_clients_sales(date_str, date_str, spot_id)
                save_clients(clients_sales)
                
                transactions = api_client.get_transactions(date_str, date_str, spot_id)
                save_transactions(transactions)

                if transactions:
                    tx_ids = [tx.get("transaction_id") for tx in transactions if tx.get("transaction_id")]
                    
                    tx_products = api_client.get_transactions_products(tx_ids)
                    save_transactions_products(tx_products)
                    
                    self.stdout.write(f"Syncing history for {len(tx_ids)} transactions...")
                    for tx_id in tx_ids:
                        history = api_client.make_request(
                            "GET", "dash.getTransactionHistory", params={"transaction_id": tx_id}
                        ).get("response", [])
                        save_transaction_history(tx_id, history)
                
                save_shift_sales_to_db(api_client, date_str, spot_id)

            self.stdout.write(self.style.SUCCESS(f"Transactional data for {date_str} synced."))

        except Exception as e:
            logger.error(f"Error during data sync for {date_str}: {e}", exc_info=True)
            self.stderr.write(self.style.ERROR(f"Error during data sync: {e}"))
            if not options['force_salary']:
                self.stderr.write(self.style.ERROR("Aborting salary calculation due to sync error."))
                return 

        if not options['skip_salary']:
            self.stdout.write(f"Calculating salaries for {date_str}...")
            
            shifts_for_day = Shift.objects.filter(date=date_obj)
            
            if not shifts_for_day.exists():
                self.stdout.write(self.style.WARNING(
                    f"No employee shifts (Shift models) found for {date_str}. No salaries to calculate."
                ))
            else:
                self.stdout.write(f"Found {shifts_for_day.count()} shifts. Calculating salaries...")
                count = 0
                for shift in shifts_for_day:
                    try:
                        calculate_and_save_shift_salaries(shift)
                        count += 1
                    except Exception as e:
                        self.stderr.write(self.style.ERROR(f"Error calculating salary for shift {shift.id}: {e}"))
                self.stdout.write(self.style.SUCCESS(f"Salaries calculated and saved for {count} shifts."))
        else:
            self.stdout.write("Skipping salary calculation.")
            
        self.stdout.write(self.style.SUCCESS(f"=== Daily sync for {date_str} complete. ==="))