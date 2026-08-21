"""Server-validated forms for account workflows."""

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from accounts.models import Account
from accounts.security import canonicalize_account_email, request_origin
from accounts.services.registration import register_account
from accounts.services.throttling import (
    evaluate_login_throttle,
    record_login_failure,
    record_login_success,
    serialized_login_attempt,
)

GENERIC_LOGIN_FAILURE = "No fue posible iniciar sesión con los datos proporcionados."
GENERIC_REGISTRATION_FAILURE = "No fue posible crear la cuenta con esos datos."


class RoleSearchForm(forms.Form):
    q = forms.CharField(
        label="Buscar cuentas",
        max_length=100,
        required=False,
        strip=True,
    )


class ProfileForm(forms.ModelForm):
    display_name = forms.CharField(
        label="Nombre visible",
        min_length=1,
        max_length=100,
        strip=True,
    )

    class Meta:
        model = Account
        fields = ("display_name",)

    def save(self, commit=True):
        account = super().save(commit=False)
        if commit:
            account.save(update_fields=("display_name",))
        return account


class RegistrationForm(forms.Form):
    email = forms.EmailField(
        label="Correo electrónico",
        max_length=254,
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
    )
    display_name = forms.CharField(label="Nombre visible", max_length=100)
    password1 = forms.CharField(
        label="Contraseña",
        help_text="Usa al menos 15 caracteres.",
        max_length=128,
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    password2 = forms.CharField(
        label="Confirmar contraseña",
        max_length=128,
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    def clean_email(self):
        email = canonicalize_account_email(self.cleaned_data["email"])
        if Account.objects.filter(email=email).exists():
            raise ValidationError(GENERIC_REGISTRATION_FAILURE)
        return email

    def clean_display_name(self):
        display_name = self.cleaned_data["display_name"].strip()
        if not display_name:
            raise ValidationError("El nombre visible es obligatorio.")
        return display_name

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            self.add_error("password2", "Las contraseñas no coinciden.")
        if password1:
            candidate = Account(
                email=cleaned_data.get("email", ""),
                display_name=cleaned_data.get("display_name", ""),
            )
            try:
                validate_password(password1, user=candidate)
            except ValidationError as exc:
                self.add_error("password1", exc)
        return cleaned_data

    def save(self):
        return register_account(
            email=self.cleaned_data["email"],
            display_name=self.cleaned_data["display_name"],
            password=self.cleaned_data["password1"],
        )


class ThrottledAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(label="Correo electrónico", max_length=254)
    password = forms.CharField(
        label="Contraseña",
        max_length=128,
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )
    next = forms.CharField(required=False, widget=forms.HiddenInput)

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        self.retry_after = 0

    def clean(self):
        # Throttling must run before AuthenticationForm evaluates credentials.
        cleaned_data = forms.Form.clean(self)
        username = cleaned_data.get("username")
        password = cleaned_data.get("password")
        if not username or not password:
            return cleaned_data

        canonical_email = canonicalize_account_email(username)
        origin = request_origin(self.request)
        with serialized_login_attempt(canonical_email, origin):
            self.retry_after = evaluate_login_throttle(canonical_email, origin)
            if not self.retry_after:
                self.user_cache = authenticate(
                    self.request,
                    username=canonical_email,
                    password=password,
                )
                if self.user_cache is not None:
                    try:
                        self.confirm_login_allowed(self.user_cache)
                    except ValidationError:
                        self.user_cache = None
                if self.user_cache is None:
                    record_login_failure(canonical_email, origin)
                else:
                    record_login_success(canonical_email)

        if self.retry_after or self.user_cache is None:
            raise ValidationError(GENERIC_LOGIN_FAILURE)
        cleaned_data["username"] = canonical_email
        return cleaned_data
