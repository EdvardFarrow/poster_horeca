import asyncio
from datetime import datetime as dt
import json
from typing import Optional
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from asgiref.sync import sync_to_async, async_to_sync

from .client import PosterAPIClient
from .serializers import CashShiftSerializer, ShiftSalesSerializer, TransactionHistorySerializer
import logging

logger = logging.getLogger(__name__)


class StatisticsView(viewsets.ViewSet):
    def list(self, request):
        type_ = request.query_params.get("type", "waiters")
        date_from = request.query_params.get("dateFrom")
        date_to = request.query_params.get("dateTo")
        entity_id = request.query_params.get("id")

        logger.info(f"Received params: {request.query_params}")

        client = PosterAPIClient()

        try:
            if type_ == "products":
                raw_data = client.get_products_sales(date_from=date_from, date_to=date_to, spot_id=entity_id)
            elif type_ == "categories":
                raw_data = client.get_categories_sales(date_from=date_from, date_to=date_to, spot_id=entity_id)
            elif type_ == "waiters":
                raw_data = client.get_waiters_sales(date_from=date_from, date_to=date_to, spot_id=entity_id)
            elif type_ == "clients":
                raw_data = client.get_clients_sales(date_from=date_from, date_to=date_to, spot_id=entity_id)
            

            else:
                return Response(
                    {"error": f"Unknown type '{type_}'"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer = StatisticsResponseSerializer({"type": type_, "data": raw_data})
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)





class CashShiftViewSet(viewsets.ViewSet):
    def list(self, request):
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
    def list(self, request):
        date = request.query_params.get('date')
        if not date:
            date = dt.today().strftime('%Y-%m-%d')

        spot_id = request.query_params.get('spot_id')
        if spot_id:
            try:
                spot_id = int(spot_id)
            except ValueError:
                return Response(
                    {"error": f"Неверный spot_id: {spot_id}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        client = PosterAPIClient()

        try:
            data = client.get_sales_by_shift_with_delivery(date=date, spot_id=spot_id)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        if not data:
            return Response([], status=status.HTTP_200_OK)

        serialized_data = []
        for shift_id, sales in data.items():
            serialized_data.append({
                'poster_shift_id': shift_id,
                'regular': sales.get('regular', []),
                'delivery': sales.get('delivery', []),
                'difference': sales.get('difference', 0),
                'tips': sales.get('tips', 0.0),
                'tips_by_service': sales.get('tips_by_service', {})

            })

        serializer = ShiftSalesSerializer(serialized_data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)






class TransactionsHistoryViewSet(viewsets.ViewSet):

    def list(self, request):
        return async_to_sync(self._async_list)(request)

    async def _async_list(self, request):
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
        serializer = PaymentIDsSerialzer(payments_data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    
