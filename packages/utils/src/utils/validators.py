import re

_CNPJ_RE = re.compile(r"^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$")
_PHONE_E164_RE = re.compile(r"^\+\d{7,15}$")


def is_valid_cnpj_format(value: str) -> bool:
    """Valida formato XX.XXX.XXX/XXXX-XX (não verifica dígitos verificadores)."""
    return bool(_CNPJ_RE.match(value))


def is_valid_e164(phone: str) -> bool:
    """Valida formato E.164: +<código país><número>."""
    return bool(_PHONE_E164_RE.match(phone))
