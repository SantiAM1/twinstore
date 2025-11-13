import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

class StrongPasswordValidator:
    def validate(self, password, user=None):
        if len(password) < 8:
            raise ValidationError(_("La contraseña debe tener al menos 8 caracteres."))

        if not re.search(r"[A-ZÁÉÍÓÚÑ]", password):
            raise ValidationError(_("La contraseña debe contener al menos una letra mayúscula."))

        if not re.search(r"\d", password):
            raise ValidationError(_("La contraseña debe contener al menos un número."))

        if not re.search(r"[^A-Za-z0-9]", password):
            raise ValidationError(_("La contraseña debe contener al menos un carácter especial."))

    def get_help_text(self):
        return _(
            "La contraseña debe tener al menos 8 caracteres, una mayúscula, un número y un carácter especial."
        )
