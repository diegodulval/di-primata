class OficinaDomainError(Exception):
    """Base para todas as exceções de domínio. Nunca importar HTTPException aqui."""


class NaoEncontrado(OficinaDomainError):
    pass


class SemPermissao(OficinaDomainError):
    pass


class CredenciaisInvalidas(OficinaDomainError):
    pass


class UsuarioInativo(OficinaDomainError):
    pass


class EmailJaCadastrado(OficinaDomainError):
    pass


class WhatsappJaCadastrado(OficinaDomainError):
    pass


class MecanicoObrigatorio(OficinaDomainError):
    """Tentativa de mover OS para EM_EXECUCAO sem mecânico atribuído."""


class TransicaoInvalida(OficinaDomainError):
    """Transição de status de OS não permitida."""


class EstoqueInsuficiente(OficinaDomainError):
    pass


class OSJaFechada(OficinaDomainError):
    pass


class WhatsappObrigatorioParaMecanico(OficinaDomainError):
    """MECANICO deve ter numero_whatsapp — é sua interface principal."""


class PlacaInvalida(OficinaDomainError):
    """Formato de placa não reconhecido (esperado: ABC1234 ou ABC1D23)."""


class NFeJaImportada(OficinaDomainError):
    """Tentativa de importar NF-e com chave que já existe no banco."""


class RascunhoPendente(OficinaDomainError):
    """Tentativa de confirmar NF-e com itens ainda pendentes de vinculação."""


class RascunhoJaConfirmado(OficinaDomainError):
    """Tentativa de operar em rascunho já confirmado ou cancelado."""


class EntradaJaProcessada(OficinaDomainError):
    """Tentativa de editar ou processar entrada que já está PROCESSADA."""
