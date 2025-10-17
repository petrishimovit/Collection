from rest_framework.routers import DefaultRouter
from collection.views.collection import CollectionViewSet

router = DefaultRouter()
router.register(r"collections", CollectionViewSet, basename="Read Collection")

urlpatterns = router.urls
