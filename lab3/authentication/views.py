from .models import SignupForm
from django.shortcuts import redirect, render
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages

def signup(request):
    context = {}

    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()

            login(request, user)
            return redirect('index')
        else:
            messages.error(request, "signup is not valid")
            context["form_errors"] = form.errors

    form = SignupForm()
    context["form"] = form
    return render(request, 'authentication/signup.html', context)


def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('index')
        else:
            messages.error(request, 'change password is not valid')

    form = PasswordChangeForm(request.user)
    return render(request, 'authentication/change_password.html', {
        'form': form
    })