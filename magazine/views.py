from rest_framework import viewsets, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from .models import Article, Category, Tag, Author, Magazine
from .serializers import (
    ArticleListSerializer, ArticleDetailSerializer, CategorySerializer, 
    TagSerializer, AuthorSerializer, MagazineSerializer
)


class ArticleViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = Article.objects.select_related('author', 'category').prefetch_related('tags').all()
	lookup_field = 'slug'
	filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
	filterset_fields = ['category__slug', 'tags__slug']
	search_fields = ['title', 'excerpt', 'content']
	ordering_fields = ['date', 'views', 'likes']

	def get_serializer_class(self):
		if self.action == 'retrieve':
			return ArticleDetailSerializer
		return ArticleListSerializer

	@action(detail=True, methods=['post'])
	def increment_views(self, request, slug=None):
		article = self.get_object()
		article.views = article.views + 1
		article.save(update_fields=['views'])
		return Response({'views': article.views})


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = Category.objects.all()
	serializer_class = CategorySerializer


class TagViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = Tag.objects.all()
	serializer_class = TagSerializer


class AuthorViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = Author.objects.all()
	serializer_class = AuthorSerializer


class MagazineViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = Magazine.objects.filter(is_active=True)
	serializer_class = MagazineSerializer
	lookup_field = 'slug'
	filter_backends = [filters.OrderingFilter]
	ordering_fields = ['published_date']
	ordering = ['-published_date']

	def get_queryset(self):
		return super().get_queryset().order_by('-published_date')
