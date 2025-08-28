from requests import request
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from .client import PosterAPIClient
from .serializers import AnalyticsResponseSerializer


class AnalyticsView(viewsets.ViewSet):
    def list(self, request):
        type_ = request.query_params.get("type", "waiters")
        select_param = request.query_params.get("select", "revenue")
        select = [s.strip() for s in select_param.split(",")] if select_param else ["revenue"]

        date_from = request.query_params.get("dateFrom")
        date_to = request.query_params.get("dateTo")
        entity_id = request.query_params.get("id")
        interpolate = request.query_params.get("interpolate", "day")
        business_day = request.query_params.get("business_day", "false").lower() == "true"

        client = PosterAPIClient(fiscal=0)

        try:
            raw_data = client.get_analytics(
                type_=type_,
                select=select,
                date_from=date_from,
                date_to=date_to,
                entity_id=entity_id,
                interpolate=interpolate,
                business_day=business_day
            )

            serializer = AnalyticsResponseSerializer({
                "type": type_,
                "data": raw_data
            })
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
