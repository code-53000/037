from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BoothApplicationViewSet

router = DefaultRouter()
router.register(r'', BoothApplicationViewSet, basename='application')

urlpatterns = [
    path('', include(router.urls)),
]
