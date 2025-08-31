from rest_framework import viewsets, status
from rest_framework.response import Response
from .client import PosterAPIClient
from .serializers import AnalyticsResponseSerializer


class AnalyticsView(viewsets.ViewSet):
    def list(self, request):
        type_ = request.query_params.get("type", "waiters")
        date_from = request.query_params.get("dateFrom")
        date_to = request.query_params.get("dateTo")
        entity_id = request.query_params.get("id")

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

            serializer = AnalyticsResponseSerializer({"type": type_, "data": raw_data})
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
