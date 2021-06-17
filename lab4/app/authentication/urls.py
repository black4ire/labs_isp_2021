from django.urls import path
from . import views
from django.contrib.auth.views import LoginView

urlpatterns = [
    path("signup", views.signup, name="signup"),
    path("login", LoginView.as_view(redirect_authenticated_user=True), name="login"),
    path("change-password", views.change_password, name="change_password"),
    path("reset-password", views.reset_password, name="reset_password"),
    path(
        "complete-password-reset/<uidb64>/<token>",
        views.complete_password_reset,
        name="complete_password_reset",
    ),
]
