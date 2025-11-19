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

    def get_serializer_context(self):
        context = super().get_serializer_context()
        # Print debug info
        if self.request:
            print(f"[Magazine] Request scheme: {self.request.scheme}")
            print(f"[Magazine] Request host: {self.request.get_host()}")
            print(f"[Magazine] Request path: {self.request.path}")
        return context

    @action(detail=False, methods=['get'], permission_classes=[])
    def featured_campaigns(self, request):
        """Get featured active campaigns for magazine sidebar"""
        from django.utils import timezone
        from django.db.models import Q
        from promotions.models import SponsorCampaign
        from promotions.serializers import SponsorCampaignSerializer
        
        now = timezone.now()
        campaigns = SponsorCampaign.objects.filter(
            status='active',
            start_date__lte=now,
            end_date__gte=now,
            priority_level__gte=2  # Only high and premium campaigns
        ).select_related('sponsored_post', 'sponsor').order_by('-priority_level', '-created_at')[:5]
        
        serializer = SponsorCampaignSerializer(campaigns, many=True, context={'request': request})
        return Response({'results': serializer.data})