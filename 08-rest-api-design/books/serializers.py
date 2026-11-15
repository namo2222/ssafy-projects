from rest_framework import serializers
from .models import Book, Category, Comment, Thread


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name')


class BookListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ('id', 'title', 'author', 'isbn', 'cover')


class ThreadSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Thread
        fields = ('id', 'title', 'content', 'reading_date')


class BookDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    threads = ThreadSummarySerializer(many=True, read_only=True)
    num_of_threads = serializers.IntegerField(source='threads.count', read_only=True)

    class Meta:
        model = Book
        fields = '__all__'


class BookTitleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ('title',)


class ThreadListSerializer(serializers.ModelSerializer):
    book = BookTitleSerializer(read_only=True)

    class Meta:
        model = Thread
        fields = ('id', 'title', 'book')


class CommentSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ('id', 'content', 'created_at', 'updated_at')


class ThreadDetailSerializer(serializers.ModelSerializer):
    book = BookTitleSerializer(read_only=True)
    comments = CommentSummarySerializer(many=True, read_only=True)
    num_of_comments = serializers.IntegerField(source='comments.count', read_only=True)

    class Meta:
        model = Thread
        fields = '__all__'


class CommentDetailSerializer(CommentSummarySerializer):
    thread = serializers.CharField(source='thread.title', read_only=True)

    class Meta(CommentSummarySerializer.Meta):
        fields = CommentSummarySerializer.Meta.fields + ('thread',)
