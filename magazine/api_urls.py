from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import (
    ArticleViewSet, CategoryViewSet, TagViewSet, 
    AuthorViewSet, MagazineViewSet
)

router = DefaultRouter()
router.register(r'articles', ArticleViewSet, basename='article')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'authors', AuthorViewSet, basename='author')
router.register(r'magazines', MagazineViewSet, basename='magazine')

urlpatterns = [
    path('', include(router.urls)),
]
