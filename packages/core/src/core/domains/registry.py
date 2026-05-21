from core.domains.industrial import INDUSTRIAL
from core.domains.rural import RURAL
from core.domains.schema import DomainSchema

_INDUSTRIAL_KEYS = {
    "industrial", "industria", "manufatura", "fabrica",
    "textil", "metalurgica", "alimenticia", "quimica", "moveleira",
}

# Agrupa todas as setor_options de todos os domínios para o formulário de cadastro
ALL_SETOR_OPTIONS = [
    *RURAL.setor_options,
    *INDUSTRIAL.setor_options,
]


def resolve_domain(setor_primario: str) -> DomainSchema:
    """Resolve o DomainSchema a partir do setor_primario da conta."""
    normalized = setor_primario.lower().replace(" ", "").replace("-", "")
    for key in _INDUSTRIAL_KEYS:
        if key in normalized:
            return INDUSTRIAL
    return RURAL
