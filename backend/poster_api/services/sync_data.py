if __name__ == "__main__":
    from poster_api.client import PosterAPIClient  
    import logging
    from poster_api.services.saving import sync_all_from_date
    from decouple import config
    
    api_token = config("POSTER_API_TOKEN")

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    api_client = PosterAPIClient(api_token=api_token)
    sync_all_from_date(api_client, start_date="2025-09-01", spot_id=1)
