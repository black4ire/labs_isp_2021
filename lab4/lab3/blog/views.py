from django.contrib.auth import logout, login
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import AdditionalUserFeatures, Category, Post
from .forms import PostForm
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required

def empty_page(request):
    return render(
        request,
        'blog/empty_page.html',
        {}
    )

def post_list(request):
    posts = Post.objects.filter(published_date__lte=timezone.now()).order_by('-published_date')
    return render(request, 'blog/post_list.html', {'posts': posts})

def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    can_edit = post.author.username == request.user.username
    return render(request, 'blog/post_detail.html', {'post': post, 'can_edit': can_edit})

@login_required(login_url='login')
def post_new(request):
    error_title = None
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES)
        print("Files: ", request.FILES)
        print("POST: ", request.POST)
        if form.is_valid():
            post = form.save(commit=False)

            post.author = request.user
            post.published_date = timezone.now()

            new_cats = []
            catnames =  [cat.name for cat in Category.objects.all()]
            for name in catnames:
                if name in request.POST.keys():
                    cat = Category.objects.get(name=name)
                    new_cats.append(cat)
            post.save()
            post.categories.set(new_cats)
            return redirect('post_detail', pk=post.pk)
        else:
            title = request.POST['title'].strip()
            if Post.objects.filter(title=title).exists():
                error_title = "Такой заголовок уже существует."
    else:
        form = PostForm()
    categories = Category.objects.all()
    return render(
        request,
        'blog/post_edit.html',
        {'form': form, 'error_title': error_title, 'categories': categories}
    )

@login_required(login_url='login')
def post_edit(request, pk):
    error_title = None
    post = get_object_or_404(Post, pk=pk)
    can_edit = post.author.username == request.user.username
    if not can_edit:
        return redirect('post_detail', pk=post.pk)
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES, instance=post)
        print("POST: ", request.POST)
        if form.is_valid():
            print('Form is valid.')
            post = form.save(commit=False)
            post.author = request.user
            post.published_date = timezone.now()

            new_cats = []
            catnames =  [cat.name for cat in Category.objects.all()]
            for name in catnames:
                if name in request.POST.keys():
                    cat = Category.objects.get(name=name)
                    new_cats.append(cat)
            post.categories.set(new_cats)

            post.save()
            return redirect('post_detail', pk=post.pk)
        else:
            title = request.POST['title'].strip()
            if Post.objects.filter(title=title).exists():
                error_title = "Такой заголовок уже существует."
    else:
        form = PostForm(instance=post)
    categories = Category.objects.all()
    return render(
        request,
        'blog/post_edit.html',
        {'form': form, 'error_title': error_title, 'categories': categories}
    )

@login_required(login_url='login')
def post_delete(request, pk):
    post = get_object_or_404(Post, pk=pk)
    can_edit = post.author.username == request.user.username
    if not can_edit:
        return redirect('post_detail', pk=post.pk)
    else:
        post.delete()
        return redirect('post_list')

def register_user(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            features = AdditionalUserFeatures()
            features.user = user
            user.save()
            features.save()
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

@login_required(login_url='login')
def post_toggle_favourite(request, pk):
    fav_post = request.user.features.favourite_post
    this_post = get_object_or_404(Post.objects.filter(author=request.user), pk=pk)
    if fav_post is not None:
        if fav_post == this_post:
            request.user.features.favourite_post = None
        else:
            request.user.features.favourite_post = this_post
    else:
        request.user.features.favourite_post = this_post
    request.user.features.save()
    return redirect('post_detail', pk=pk)
