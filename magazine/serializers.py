from rest_framework import serializers
from .models import Article, Category, Tag, Author, Magazine


class AuthorSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = Author
        fields = ('id', 'name', 'avatar', 'role', 'bio')

    def get_avatar(self, obj):
        request = self.context.get('request')
        if obj.avatar and hasattr(obj.avatar, 'url'):
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'description')


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class ArticleListSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    image = serializers.SerializerMethodField()
    pdf = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = ('id', 'title', 'slug', 'excerpt', 'image', 'pdf', 'author', 'category', 'tags', 'date', 'read_time', 'views', 'likes')

    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image and hasattr(obj.image, 'url'):
            return request.build_absolute_uri(obj.image.url) if request else obj.image.url
        return None

    def get_pdf(self, obj):
        request = self.context.get('request')
        if obj.pdf and hasattr(obj.pdf, 'url'):
            return request.build_absolute_uri(obj.pdf.url) if request else obj.pdf.url
        return None


class ArticleDetailSerializer(ArticleListSerializer):
    content = serializers.CharField()

    class Meta(ArticleListSerializer.Meta):
        fields = ArticleListSerializer.Meta.fields + ('content',)


class MagazineSerializer(serializers.ModelSerializer):
    cover_image = serializers.SerializerMethodField()
    pdf_file = serializers.SerializerMethodField()

    class Meta:
        model = Magazine
        fields = ('id', 'title', 'issue', 'slug', 'description', 'cover_image', 
                 'pdf_file', 'pages', 'published_date', 'is_active')

    def get_cover_image(self, obj):
        request = self.context.get('request')
        if obj.cover_image and hasattr(obj.cover_image, 'url'):
            if request:
                url = request.build_absolute_uri(obj.cover_image.url)
                print(f"[Magazine] Cover image URL: {url}")  # Debug log
                return url
            return obj.cover_image.url
        return None

    def get_pdf_file(self, obj):
        request = self.context.get('request')
        if obj.pdf_file and hasattr(obj.pdf_file, 'url'):
            if request:
                url = request.build_absolute_uri(obj.pdf_file.url)
                print(f"[Magazine] PDF file URL: {url}")  # Debug log
                return url
            return obj.pdf_file.url
        return None
