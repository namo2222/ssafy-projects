from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods
from .forms import BookForm
from .models import Book
from django.core.exceptions import PermissionDenied
from .models import Book, Thread
from .forms import BookForm, ThreadForm
from .ai import generate_questions

def index(request):
    books = Book.objects.all()

    context = {
        'books': books,
    }
    return render(request, 'books/index.html', context)

@login_required
@require_http_methods(['GET', 'POST'])
def create(request):
    if request.method == 'POST':
        form = BookForm(request.POST)

        if form.is_valid():
            book = form.save(commit=False)
            book.user = request.user
            book.save()
            return redirect('books:detail', book.pk)
    else:
        form = BookForm()

    return render(request, 'books/create.html', {'form': form})


@require_GET
def detail(request, book_pk):
    book = get_object_or_404(Book, pk=book_pk)
    return render(request, 'books/detail.html', {'book': book})

@login_required
@require_http_methods(['GET', 'POST'])
def update(request, book_pk):
    book = get_object_or_404(Book, pk=book_pk)

    if request.user != book.user:
        raise PermissionDenied

    if request.method == 'POST':
        form = BookForm(request.POST, instance=book)
        if form.is_valid():
            form.save()
            return redirect('books:detail', book.pk)
    else:
        form = BookForm(instance=book)

    return render(request, 'books/update.html', {'form': form, 'book': book})


@login_required
@require_http_methods(['POST'])
def delete(request, book_pk):
    book = get_object_or_404(Book, pk=book_pk)

    if request.user != book.user:
        raise PermissionDenied

    book.delete()
    return redirect('books:index')

@login_required
@require_http_methods(['GET', 'POST'])
def thread_create(request, book_pk):
    book = get_object_or_404(Book, pk=book_pk)

    if request.method == 'POST':
        form = ThreadForm(request.POST)

        if form.is_valid():
            thread = form.save(commit=False)
            thread.book = book          # 어느 책에 쓴 글인지
            thread.user = request.user  # 누가 글을 썼는지
            thread.save()
            return redirect('books:thread_detail', thread.pk)
    else:
        form = ThreadForm()

    return render(request, 'books/thread_create.html', {
        'form': form,
        'book': book,
    })


@require_GET
def thread_detail(request, thread_pk):
    thread = get_object_or_404(Thread, pk=thread_pk)
    context = {'thread': thread}

    if request.user == thread.user:
        result = request.session.get('thread_ai_result', {})
        if result.get('thread_pk') == thread.pk:
            context['ai_result'] = result

    return render(request, 'books/thread_detail.html', context)

@login_required
@require_http_methods(['GET', 'POST'])
def thread_update(request, thread_pk):
    thread = get_object_or_404(Thread, pk=thread_pk)

    if request.user != thread.user:
        raise PermissionDenied

    if request.method == 'POST':
        form = ThreadForm(request.POST, instance=thread)
        if form.is_valid():
            form.save()
            return redirect('books:thread_detail', thread.pk)
    else:
        form = ThreadForm(instance=thread)

    return render(request, 'books/thread_update.html', {
        'form': form,
        'thread': thread,
    })


@login_required
@require_http_methods(['POST'])
def thread_delete(request, thread_pk):
    thread = get_object_or_404(Thread, pk=thread_pk)

    if request.user != thread.user:
        raise PermissionDenied

    # 삭제 후 돌아갈 도서의 번호를 미리 보관
    book_pk = thread.book_id
    thread.delete()
    return redirect('books:detail', book_pk)

@login_required
@require_http_methods(['POST'])
def like(request, thread_pk):
    thread = get_object_or_404(Thread, pk=thread_pk)

    if thread.like_users.filter(pk=request.user.pk).exists():
        thread.like_users.remove(request.user)
    else:
        thread.like_users.add(request.user)

    return redirect('books:thread_detail', thread.pk)

@login_required
@require_http_methods(['POST'])
def thread_questions(request, thread_pk):
    thread = get_object_or_404(Thread, pk=thread_pk)

    if request.user != thread.user:
        raise PermissionDenied

    try:
        request.session['thread_ai_result'] = {
            'thread_pk': thread.pk,
            'questions': generate_questions(thread),
        }
    except ValueError as error:
        request.session['thread_ai_result'] = {
            'thread_pk': thread.pk,
            'error': str(error),
        }

    return redirect('books:thread_detail', thread.pk)