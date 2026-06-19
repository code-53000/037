from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ExhibitionViewSet

router = DefaultRouter()
router.register(r'', ExhibitionViewSet, basename='exhibition')

urlpatterns = [
    path('', include(router.urls)),
]
