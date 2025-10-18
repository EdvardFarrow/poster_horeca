from datetime import datetime as dt
from rest_framework import viewsets, status
from rest_framework.response import Response
from asgiref.sync import  async_to_sync
from rest_framework.permissions import AllowAny
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from .models import Product, ShiftSale, Spot, Workshop

from .client import PosterAPIClient
from .serializers import (
    CashShiftSerializer,
    PaymentMethodSerializer, 
    ProductForFrontendSerializer,
    ShiftSaleItemSerializer, 
    ShiftSalesSerializer,
    SpotSerializer, 
    TransactionHistorySerializer,
    WorkshopForFrontendSerializer, 
    
    )
import logging

logger = logging.getLogger(__name__)


class CashShiftViewSet(viewsets.ViewSet):
    """
    Provides an endpoint to list cash shifts from the external Poster API.
    """
    
    @method_decorator(cache_page(60 * 15))
    def list(self, request):
        """
        Retrieves a list of cash shifts from the Poster API based on query parameters.

        Args:
            request: The DRF request object.

        Query Params:
            dateFrom (str): The start date (e.g., 'YYYY-MM-DD').
            dateTo (str): The end date (e.g., 'YYYY-MM-DD').
            spot_id (int, optional): The ID of the spot to filter by.

        Returns:
            Response: A list of serialized cash shift data or an error message.
        """
        date_from = request.query_params.get("dateFrom")
        date_to = request.query_params.get("dateTo")
        spot_id = request.query_params.get("spot_id") 

        client = PosterAPIClient()
        logger.info(f"Received params: {request.query_params}")
        try:
            raw_shifts = client.get_cash_shifts(date_from=date_from, date_to=date_to, spot_id=spot_id)

            serializer = CashShiftSerializer(raw_shifts, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ShiftSalesView(viewsets.ViewSet):
    """
    Provides the main sales report endpoint.

    This view fetches detailed sales data (regular and delivery) from the
    Poster API, aggregates it across multiple spots, and then syncs
    the results with the local `ShiftSale` database model.
    It performs a 'get or create' operation for each shift.
    """

    @method_decorator(cache_page(60 * 15))
    def list(self, request):
        """
        Retrieves and aggregates sales data for a given date across multiple spots.

        It fetches data from the Poster API, then finds or creates a corresponding
        `ShiftSale` record in the local database to get a local primary key.

        Args:
            request: The DRF request object.

        Query Params:
            date (str, optional): The target date in 'YYYY-MM-DD' format. Defaults to the current day.
            spot_id (list[int], optional): A list of spot IDs to fetch. Can be provided multiple times (e.g., ?spot_id=1&spot_id=2). Defaults to ['1', '2'].

        Returns:
            Response: A list of serialized shift sales data, including local DB IDs and aggregated sales items.
        """
        date_str = request.query_params.get('date') or dt.today().strftime('%Y-%m-%d')
        
        spot_ids = request.query_params.getlist('spot_id', ['1', '2'])
        
        client = PosterAPIClient()
        total_poster_data = {}

        for spot_id in spot_ids:
            try:
                spot_id = int(spot_id)
            except (ValueError, TypeError):
                logger.warning(f"Неверный spot_id '{spot_id}' был пропущен.")
                continue

            try:
                data_for_spot = client.get_sales_by_shift_with_delivery(date=date_str, spot_id=spot_id)
                
                for shift_id, sales in data_for_spot.items():
                    if shift_id not in total_poster_data:
                        total_poster_data[shift_id] = sales
                    else:
                        total_poster_data[shift_id]['regular'].extend(sales.get('regular', []))
                        total_poster_data[shift_id]['delivery'].extend(sales.get('delivery', []))

            except Exception as e:
                logger.error(f"Ошибка при получении данных для спота {spot_id}: {e}", exc_info=True)
                continue

        if not total_poster_data:
            return Response([], status=status.HTTP_200_OK)

        poster_shift_ids = list(total_poster_data.keys())
        
        existing_shifts = ShiftSale.objects.filter(shift_id__in=poster_shift_ids)
        
        shifts_map = {shift.shift_id: shift for shift in existing_shifts}

        serialized_data = []
        date_obj = dt.strptime(date_str, '%Y-%m-%d').date()

        for shift_id, sales in total_poster_data.items():
            shift_obj = shifts_map.get(str(shift_id)) 

            if not shift_obj:
                shift_obj = ShiftSale.objects.create(shift_id=shift_id, date=date_obj)
                logger.info(f"Создана новая запись в БД для смены с ID: {shift_id}")

            serialized_data.append({
                'shift_id': shift_obj.id, 
                'regular': sales.get('regular', []),
                'delivery': sales.get('delivery', []),
                'difference': sales.get('difference', 0),
                'tips': sales.get('tips', 0.0),
                'tips_by_service': sales.get('tips_by_service', {})
            })

        serializer = ShiftSalesSerializer(serialized_data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)




class TransactionsHistoryViewSet(viewsets.ViewSet):
    """
    Provides an endpoint for fetching detailed transaction histories.
    This viewset uses an asynchronous method to communicate with the Poster API.
    """
    def list(self, request):
        """
        Synchronously wraps the asynchronous `_async_list` method.
        This is the main entry point for the 'list' action.

        Args:
            request: The DRF request object.

        Returns:
            Response: The result of the async list call.
        """
        return async_to_sync(self._async_list)(request)

    async def _async_list(self, request):
        """
        Asynchronously retrieves all transactions for a given date range.

        Args:
            request: The DRF request object.

        Query Params:
            date_from (str): The start date/time (e.g., 'YYYY-MM-DD'). Required.
            date_to (str): The end date/time (e.g., 'YYYY-MM-DD'). Required.
            spot_id (int, optional): The ID of the spot to filter by.

        Returns:
            Response: A list of serialized transaction data or an error message.
        """
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")
        spot_id = request.query_params.get("spot_id")

        if not date_from or not date_to:
            return Response({"error": "date_from and date_to are required"}, status=400)

        spot_id_int = int(spot_id) if spot_id else None
        client = PosterAPIClient()

        try:
            transactions = await client.get_full_transactions_for_day(
                date_from=date_from,
                date_to=date_to,
                spot_id=spot_id_int
            )
            serializer = TransactionHistorySerializer(transactions, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"[TRANSACTIONS_HISTORY] Failed: {e}", exc_info=True)
            return Response({"error": "Failed to fetch transactions"}, status=500)


class PaymentMethodsView(viewsets.ViewSet):
    def list(self, request, *args, **kwargs):
        client = PosterAPIClient()
        payments_data = client.get_payments_id()
        serializer = PaymentMethodSerializer(payments_data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class WorkshopViewSet(viewsets.ModelViewSet):
    queryset = Workshop.objects.all()
    serializer_class = WorkshopForFrontendSerializer


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductForFrontendSerializer


class SpotViewSet(viewsets.ModelViewSet):
    queryset = Spot.objects.all()
    serializer_class = SpotSerializer