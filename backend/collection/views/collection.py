from django.db.models import Count
from rest_framework import viewsets, permissions
from collection.models import Collection
from collection.serializers.collection import CollectionSerializer
from collection.pagination import DefaultPageNumberPagination


class CollectionViewSet(viewsets.ModelViewSet):
    """
    /api/collections/      -> all collections
    /api/collections/id/   -> collection by id
    /api/collections/me/   -> only current user's collections
    """
    serializer_class = CollectionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = DefaultPageNumberPagination

    def get_queryset(self):
        return (
            Collection.objects
            .all()  
            .annotate(items_count=Count("items"))
            .order_by("name", "id")  
        )

   
    from rest_framework.decorators import action
    from rest_framework import response

    @action(detail=False, methods=["get"], url_path="me", pagination_class=DefaultPageNumberPagination)
    def me(self, request):
        qs = (
            Collection.objects
            .filter(owner=request.user)
            .annotate(items_count=Count("items"))
            .order_by("name", "id")
        )
        page = self.paginate_queryset(qs)
        if page is not None:
            ser = self.get_serializer(page, many=True)
            return self.get_paginated_response(ser.data)
        ser = self.get_serializer(qs, many=True)
        return response.Response(ser.data)
    

   
    