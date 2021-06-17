from .email_thread import EmailThread
from .models import SignupForm
from django.shortcuts import redirect, render
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.core.validators import validate_email
from django.core.mail import EmailMessage
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_text
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.urls import reverse
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.exceptions import ValidationError
from .models import SetPasswordForm, SendResetEmailForm


def signup(request):
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()

            login(request, user)
            return redirect("index")
        else:
            messages.error(request, "signup is not valid")

    form = SignupForm()
    context = {"form": form}
    return render(request, "authentication/signup.html", context)


def change_password(request):
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Your password was successfully updated!")
            return redirect("index")
        else:
            messages.error(request, "change password is not valid")

    form = PasswordChangeForm(request.user)
    return render(request, "authentication/change_password.html", {"form": form})


def reset_password(request):
    context = {"form": SendResetEmailForm()}

    if request.method == "POST":
        form = SendResetEmailForm(request.POST)

        if not form.is_valid():
            messages.error(request, "Please, use valid email")
            return render(request, "authentication/reset_password.html", context)

        email = form.cleaned_data["email"]

        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, "Please, use valid email")
            return render(request, "authentication/reset_password.html", context)

        current_site = get_current_site(request)

        user = User.objects.filter(email=email)

        if not user.exists():
            messages.error(request, "No users registered with this email")
            render(request, "authentication/reset_password.html", context)

        email_content = {
            "user": user[0],
            "domain": current_site.domain,
            "uid": urlsafe_base64_encode(force_bytes(user[0].pk)),
            "token": PasswordResetTokenGenerator().make_token(user[0]),
        }

        link = reverse(
            "complete_password_reset",
            kwargs={"uidb64": email_content["uid"], "token": email_content["token"]},
        )

        email_subject = "Password reset instructions"

        reset_url = "http://" + current_site.domain + link

        # f string
        email = EmailMessage(
            email_subject,
            "Hi "
            + user[0].username
            + ", Please open the link below to reset your password \n"
            + reset_url,
            "noreply@semycolon.com",
            [email],
        )

        EmailThread(email).start()

        messages.success(request, "We send you an email with reset")

    return render(request, "authentication/reset_password.html", context)


def complete_password_reset(request, uidb64, token):
    try:
        user_id = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(id=user_id)

        if not PasswordResetTokenGenerator().check_token(user, token):
            messages.info(request, "This link is invalid, request a new link")
            return redirect("index")
    except:
        messages.error(request, "Something went wrong, request another link")
        return redirect("index")

    if request.method == "POST":
        form = SetPasswordForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Passwords do not match")
        else:
            user.set_password(form.cleaned_data["new_password1"])
            user.save()
            messages.success(request, "Password reset successful")
            return redirect("login")

    form = SetPasswordForm()
    context = {"uidb64": uidb64, "token": token, "form": form}
    # context = dict(uudi=uidb64, ...)

    return render(request, "authentication/set_new_password.html", context)
