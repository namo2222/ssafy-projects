from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as auth_login
from django.views.decorators.http import require_http_methods
from .forms import CustomUserCreationForm
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from .forms import CustomUserChangeForm


@require_http_methods(['GET', 'POST'])
def signup(request):
    # 이미 로그인했다면 도서 목록으로 이동
    if request.user.is_authenticated:
        return redirect('books:index')

    if request.method == 'POST':
        # 제출한 입력값과 프로필 사진을 Form에 전달
        form = CustomUserCreationForm(request.POST, request.FILES)

        if form.is_valid():
            # 회원 저장
            user = form.save()

            # 가입한 회원으로 바로 로그인
            auth_login(request, user)

            return redirect('books:index')

    else:
        # 처음 페이지에 접속하면 빈 Form 생성
        form = CustomUserCreationForm()

    context = {
        'form': form,
    }
    return render(request, 'accounts/signup.html', context)

@require_http_methods(['GET', 'POST'])
def login(request):
    if request.user.is_authenticated:
        return redirect('books:index')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            return redirect('books:index')
    else:
        form = AuthenticationForm(request)

    return render(request, 'accounts/login.html', {'form': form})


@require_http_methods(['POST'])
def logout(request):
    auth_logout(request)
    return redirect('books:index')

@require_http_methods(['GET'])
def profile(request, username):
    person = get_object_or_404(get_user_model(), username=username)

    return render(request, 'accounts/profile.html', {'person': person})


@login_required
@require_http_methods(['POST'])
def follow(request, username):
    person = get_object_or_404(get_user_model(), username=username)

    # 다른 사용자의 프로필에서만 팔로우 관계를 변경
    if request.user != person:
        followings = request.user.followings

        if followings.filter(pk=person.pk).exists():
            followings.remove(person)
        else:
            followings.add(person)

    return redirect('accounts:profile', username=person.username)

@login_required
@require_http_methods(['GET', 'POST'])
def update(request):
    if request.method == 'POST':
        form = CustomUserChangeForm(
            request.POST,
            request.FILES,
            instance=request.user,
        )
        if form.is_valid():
            form.save()
            return redirect('books:index')
    else:
        form = CustomUserChangeForm(instance=request.user)

    return render(request, 'accounts/update.html', {'form': form})


@login_required
@require_http_methods(['GET', 'POST'])
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            return redirect('books:index')
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'accounts/change_password.html', {'form': form})


@login_required
@require_http_methods(['POST'])
def delete(request):
    request.user.delete()
    auth_logout(request)
    return redirect('books:index')