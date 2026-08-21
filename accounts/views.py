"""HTTP adapters for account workflows."""

import logging

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.db.models import Q
from django.http import HttpResponseForbidden, HttpResponseNotFound
from django.http.response import HttpResponseRedirectBase
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from accounts.forms import (
    ProfileForm,
    RegistrationForm,
    RoleSearchForm,
    ThrottledAuthenticationForm,
)
from accounts.models import Account, RoleChangeLog
from accounts.security import (
    CONTENT_ADMIN_ROLE,
    LEARNER_ROLE,
    active_account_required,
    resolve_safe_next,
)
from accounts.services.roles import change_content_role

logger = logging.getLogger(__name__)
GENERIC_ROLE_DENIAL = "No tienes permiso para realizar esta acción."


class HttpResponseSeeOther(HttpResponseRedirectBase):
    status_code = 303


class ThrottledLoginView(LoginView):
    authentication_form = ThrottledAuthenticationForm
    template_name = "accounts/login.html"

    def get_initial(self):
        initial = super().get_initial()
        initial[self.redirect_field_name] = self.request.GET.get(
            self.redirect_field_name,
            "",
        )
        return initial

    def form_valid(self, form):
        user = form.get_user()
        login(self.request, user)
        logger.info("accounts.login.succeeded", extra={"account_id": str(user.pk)})
        destination = resolve_safe_next(
            form.cleaned_data.get(self.redirect_field_name, ""),
            request=self.request,
            user=user,
        )
        return HttpResponseSeeOther(destination)

    def form_invalid(self, form):
        event = (
            "accounts.login.throttled" if form.retry_after else "accounts.login.failed"
        )
        logger.info(event)
        response = super().form_invalid(form)
        if form.retry_after:
            response.status_code = 429
            response["Retry-After"] = str(form.retry_after)
        return response


@require_http_methods(["GET", "POST"])
def register_view(request):
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            form.save()
        except IntegrityError:
            form.add_error("email", "No fue posible crear la cuenta con esos datos.")
        else:
            messages.success(request, "La cuenta fue creada. Ya puedes iniciar sesión.")
            return HttpResponseSeeOther(reverse("accounts:login"))
    return render(request, "accounts/register.html", {"form": form})


@active_account_required
@require_http_methods(["GET", "POST"])
def profile_view(request):
    form = ProfileForm(request.POST or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        return HttpResponseSeeOther(reverse("accounts:profile"))

    group_names = set(request.user.groups.values_list("name", flat=True))
    role_labels = []
    if LEARNER_ROLE in group_names:
        role_labels.append("Aprendiz")
    if CONTENT_ADMIN_ROLE in group_names:
        role_labels.append("Administrador de contenido")
    if request.user.is_superuser:
        role_labels.append("Administrador de plataforma")
    return render(
        request,
        "accounts/profile.html",
        {"form": form, "role_labels": role_labels},
    )


@require_POST
def logout_view(request):
    logout(request)
    return HttpResponseSeeOther(reverse("accounts:login"))


@active_account_required
@require_http_methods(["GET"])
def role_management_view(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden(GENERIC_ROLE_DENIAL)

    form = RoleSearchForm(request.GET)
    accounts = Account.objects.order_by("email").prefetch_related("groups")
    if form.is_valid():
        query = form.cleaned_data["q"]
        if query:
            accounts = accounts.filter(
                Q(email__icontains=query) | Q(display_name__icontains=query)
            )
    else:
        accounts = accounts.none()

    page_obj = Paginator(accounts, 25).get_page(request.GET.get("page"))
    for account in page_obj:
        group_names = {group.name for group in account.groups.all()}
        account.has_content_role = CONTENT_ADMIN_ROLE in group_names
        account.role_labels = []
        if LEARNER_ROLE in group_names:
            account.role_labels.append("Aprendiz")
        if account.has_content_role:
            account.role_labels.append("Administrador de contenido")
        if account.is_superuser:
            account.role_labels.append("Administrador de plataforma")

    return render(
        request,
        "accounts/role_management.html",
        {"form": form, "page_obj": page_obj},
    )


def _role_change_response(request, target_ref, action):
    outcome = change_content_role(request.user, target_ref, action)
    if outcome.result == RoleChangeLog.Result.SUCCESS:
        return HttpResponseSeeOther(reverse("accounts:role-management"))
    if outcome.result == RoleChangeLog.Result.TARGET_NOT_FOUND:
        if outcome.actor_is_platform_admin:
            return HttpResponseNotFound("No se encontró el recurso solicitado.")
        return HttpResponseForbidden(GENERIC_ROLE_DENIAL)
    return HttpResponseForbidden(GENERIC_ROLE_DENIAL)


@active_account_required
@require_POST
def assign_content_role_view(request, target_ref):
    return _role_change_response(request, target_ref, RoleChangeLog.Action.ASSIGN)


@active_account_required
@require_POST
def revoke_content_role_view(request, target_ref):
    return _role_change_response(request, target_ref, RoleChangeLog.Action.REVOKE)
