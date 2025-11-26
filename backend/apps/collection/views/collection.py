from django.db import models
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response
from rest_framework import status

from apps.collection.models import Collection
from apps.collection.serializers.collection import CollectionSerializer
from apps.collection.serializers.item import ItemSerializer
from apps.collection.permissions.collection import IsCollectionOwnerOrReadOnly
from apps.collection.selectors.collection import (
    get_public_collections,
    get_collections_for_user,
    get_user_collections,
    get_collection_for_user,
    get_feed_collections_for_user,
)
from apps.collection.selectors.item import get_collection_items_for_user
from apps.collection.pagination import DefaultPageNumberPagination


class CollectionViewSet(viewsets.ModelViewSet):

    serializer_class = CollectionSerializer
    permission_classes = (IsCollectionOwnerOrReadOnly,)
    pagination_class = DefaultPageNumberPagination
    filter_backends = (OrderingFilter,)
    ordering_fields = (
        "created_at",
        "items_count",
        "total_current_value",
        "total_purchase_price",
    )
    ordering = ("-created_at",)

    
    queryset = Collection.objects.all().select_related("owner")

    def get_queryset(self):
       
        if self.action == "list":
            return get_public_collections()
      
        return get_collections_for_user(self.request.user)

    def list(self, request, *args, **kwargs):
        
        queryset = get_public_collections()
        queryset = self.filter_queryset(queryset)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
       
        collection_id = kwargs.get("pk")
        instance = get_collection_for_user(request.user, collection_id)
        if instance is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        Collection.objects.filter(pk=instance.pk).update(
            views_count=models.F("views_count") + 1
        )
        instance.refresh_from_db(fields=["views_count"])

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def update(self, request, *args, **kwargs):
        
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @action(
        detail=False,
        methods=["get"],
        url_path="my",
        permission_classes=[permissions.IsAuthenticated],
    )
    def my(self, request, *args, **kwargs):
        
        qs = get_user_collections(request.user)
        qs = self.filter_queryset(qs)

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=["get"],
        url_path="feed",
        permission_classes=[permissions.IsAuthenticated],
    )
    def feed(self, request, *args, **kwargs):
       
        qs = get_feed_collections_for_user(request.user)
        qs = self.filter_queryset(qs)

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=["get"],
        url_path="search",
    )
    def search(self, request, *args, **kwargs):
        
        q = request.query_params.get("q", "").strip()
        qs = get_collections_for_user(request.user)

        if q:
            qs = qs.filter(
                models.Q(name__icontains=q)
                | models.Q(description__icontains=q)
            )

        qs = self.filter_queryset(qs)

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get", "post"], url_path="items")
    def items(self, request, pk=None, *args, **kwargs):
        
        collection_id = pk

        if request.method.lower() == "get":
            qs = get_collection_items_for_user(request.user, collection_id)
            ordering = request.query_params.get("ordering")
            if ordering:
                qs = qs.order_by(ordering)

            page = self.paginate_queryset(qs)
            if page is not None:
                serializer = ItemSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = ItemSerializer(qs, many=True)
            return Response(serializer.data)

       
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        from apps.collection.models import Collection as CollectionModel

        try:
            collection = CollectionModel.objects.get(pk=collection_id)
        except CollectionModel.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if collection.owner != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)

        data = request.data.copy()
        data["collection"] = collection_id

        serializer = ItemSerializer(data=data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)
