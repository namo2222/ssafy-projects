from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Book, Category, Comment, Thread
from .serializers import (
    BookDetailSerializer, BookListSerializer, CategorySerializer,
    CommentDetailSerializer, ThreadDetailSerializer, ThreadListSerializer,
)


@api_view(['GET'])
def category_list(request):
    categories = Category.objects.order_by('pk')
    return Response(CategorySerializer(categories, many=True).data)


@api_view(['GET'])
def book_list(request):
    books = Book.objects.order_by('pk')
    return Response(BookListSerializer(books, many=True).data)


@api_view(['GET'])
def book_detail(request, book_pk):
    books = Book.objects.select_related('category').prefetch_related('threads')
    book = get_object_or_404(books, pk=book_pk)
    return Response(BookDetailSerializer(book).data)


@api_view(['GET'])
def thread_list(request):
    threads = Thread.objects.select_related('book').order_by('pk')
    return Response(ThreadListSerializer(threads, many=True).data)


@api_view(['POST'])
def create_thread(request, book_pk):
    book = get_object_or_404(Book, pk=book_pk)
    serializer = ThreadDetailSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save(book=book)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'DELETE'])
def thread_detail(request, thread_pk):
    thread = get_object_or_404(Thread.objects.select_related('book'), pk=thread_pk)
    if request.method == 'DELETE':
        thread.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    if request.method == 'PUT':
        serializer = ThreadDetailSerializer(thread, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    return Response(ThreadDetailSerializer(thread).data)


@api_view(['POST'])
def create_comment(request, thread_pk):
    thread = get_object_or_404(Thread, pk=thread_pk)
    serializer = CommentDetailSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save(thread=thread)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'DELETE'])
def comment_detail(request, comment_pk):
    comment = get_object_or_404(Comment.objects.select_related('thread'), pk=comment_pk)
    if request.method == 'DELETE':
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    if request.method == 'PUT':
        serializer = CommentDetailSerializer(comment, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    return Response(CommentDetailSerializer(comment).data)


@api_view(['GET'])
def book_search(request):
    query = request.query_params.get('q', '').strip()
    if not query:
        return Response({'detail': '검색어를 입력해 주세요.'}, status=status.HTTP_400_BAD_REQUEST)
    books = Book.objects.filter(Q(title__icontains=query) | Q(author__icontains=query)).order_by('pk')
    return Response(BookListSerializer(books, many=True).data)
