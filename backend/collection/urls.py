from rest_framework.routers import DefaultRouter
from collection.views.collection import CollectionViewSet
from collection.views.item import ItemViewSet

router = DefaultRouter()
router.register(r"collections", CollectionViewSet, basename="Collection")
router.register(r"items", ItemViewSet, basename="Item")


urlpatterns = router.urls
