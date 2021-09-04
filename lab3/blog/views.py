from django.contrib.auth import logout, login
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import Post
from .forms import PostForm
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required

def post_list(request):
    posts = Post.objects.filter(published_date__lte=timezone.now()).order_by('-published_date')
    return render(request, 'blog/post_list.html', {'posts': posts})

def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    can_edit = post.author.username == request.user.username
    return render(request, 'blog/post_detail.html', {'post': post, 'can_edit': can_edit})

def post_new(request):
    if request.method == "POST":
        print("Files: ", request.FILES)
        form = PostForm(request.POST, request.FILES)
        print("Files: ", request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.published_date = timezone.now()
            post.save()
            return redirect('post_detail', pk=post.pk)
    else:
        form = PostForm()
    return render(request, 'blog/post_edit.html', {'form': form})

def post_edit(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == "POST":
        print("Files: ", request.FILES)
        form = PostForm(request.POST, request.FILES, instance=post)
        print("Files: ", request.FILES)
        if form.is_valid():
            print('Form is valid.')
            post = form.save(commit=False)
            post.author = request.user
            post.published_date = timezone.now()
            post.save()
            return redirect('post_detail', pk=post.pk)
    else:
        form = PostForm(instance=post)
    return render(request, 'blog/post_edit.html', {'form': form})

def register_user(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(
        request,
        'blog/register_page.html',
        {'form': form}
    )

def login_user(request):
    if request.user.is_authenticated:
        return redirect('post_list')
    if request.method == 'POST':
        form = AuthenticationForm(request, request.POST)
        print("form: ", form.data)
        print('post: ', request.POST)
        if form.is_valid():
            user = form.get_user()
            if user is not None:
                login(request, user)
                return redirect('post_list')
    else:
        form = AuthenticationForm()
    return render(
        request,
        'blog/login_page.html',
        {'form': form}
    )

@login_required(login_url='login')
def logout_user(request):
    logout(request)
    return redirect('login')