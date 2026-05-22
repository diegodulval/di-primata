"""
Parser de XML NF-e (versão 4.00).
Retorna estruturas de dados simples — sem dependência de banco ou ORM.
"""
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

_NS = "http://www.portalfiscal.inf.br/nfe"


def _t(elem, tag: str, default: str = "") -> str:
    """Retorna o texto do primeiro filho com `tag`, ou `default`."""
    found = elem.find(f"{{{_NS}}}{tag}")
    return (found.text or default) if found is not None else default


_INVALID_EANS = {"SEM GTIN", "0", "00000000000000", "0000000000000", ""}
_RE_PRIMEIRO_TOKEN = re.compile(r'^(\S+)\s+')


def _ean_valido(ean: str) -> bool:
    return ean.strip() not in _INVALID_EANS and len(ean.strip()) >= 8


def extrair_codigo_ref(descricao: str) -> str | None:
    """Extrai o código de referência do início da descrição.

    "32208 AMORTECEDOR DIANT SUPER PLUS" → "32208"
    "CILINDRO RODA"                      → None  (sem dígito)
    "ALB2601-1809 JUNTA HOMOCINÉTICA"    → "ALB2601-1809"
    """
    m = _RE_PRIMEIRO_TOKEN.match(descricao.strip())
    if not m:
        return None
    token = m.group(1)
    if not any(c.isdigit() for c in token):
        return None
    if not 2 <= len(token) <= 25:
        return None
    return token


def _parse_date(s: str) -> date | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s).date()
    except (ValueError, TypeError):
        return None


def _d(valor: str) -> Decimal:
    """Converte string para Decimal, retorna 0 em caso de falha."""
    try:
        return Decimal(valor)
    except (InvalidOperation, TypeError):
        return Decimal("0")


@dataclass
class ItemNFe:
    codigo:         str            # cProd — código interno do fornecedor
    descricao:      str            # xProd — descrição completa
    ncm:            str
    quantidade:     Decimal
    preco_unitario: Decimal
    icms:           Decimal = Decimal("0")
    ipi:            Decimal = Decimal("0")
    ean:            str | None = None   # cEAN se válido
    codigo_ref:     str | None = None  # código extraído do início de xProd


@dataclass
class NFeParseResult:
    chave:        str
    numero:       str
    serie:        str
    data_emissao: date | None
    emit_cnpj:    str
    emit_nome:    str
    valor_total:  Decimal
    itens:        list[ItemNFe] = field(default_factory=list)


def parse_nfe(xml_bytes: bytes) -> NFeParseResult:
    """
    Parseia o conteúdo de um XML de NF-e (com ou sem nfeProc wrapper).
    Levanta ValueError se a estrutura mínima não for encontrada.
    """
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        raise ValueError(f"XML inválido: {exc}") from exc

    inf = root.find(f".//{{{_NS}}}infNFe")
    if inf is None:
        raise ValueError("Elemento infNFe não encontrado no XML")

    chave = inf.get("Id", "").removeprefix("NFe")

    ide  = inf.find(f"{{{_NS}}}ide");  ide  = ide  if ide  is not None else ET.Element("ide")
    emit = inf.find(f"{{{_NS}}}emit"); emit = emit if emit is not None else ET.Element("emit")

    data_raw = _t(ide, "dhEmi") or _t(ide, "dEmi")

    valor_elem = inf.find(f".//{{{_NS}}}ICMSTot/{{{_NS}}}vNF")
    valor_total = _d(valor_elem.text) if valor_elem is not None else Decimal("0")

    itens: list[ItemNFe] = []
    for det in inf.findall(f"{{{_NS}}}det"):
        prod = det.find(f"{{{_NS}}}prod")
        if prod is None:
            continue

        icms_elem = det.find(f".//{{{_NS}}}pICMS")
        ipi_elem  = det.find(f".//{{{_NS}}}pIPI")
        descricao = _t(prod, "xProd")
        ean_raw   = _t(prod, "cEAN")

        itens.append(ItemNFe(
            codigo=_t(prod, "cProd"),
            descricao=descricao,
            ncm=_t(prod, "NCM"),
            quantidade=_d(_t(prod, "qCom")),
            preco_unitario=_d(_t(prod, "vUnCom")),
            icms=_d(icms_elem.text) if icms_elem is not None else Decimal("0"),
            ipi=_d(ipi_elem.text)  if ipi_elem  is not None else Decimal("0"),
            ean=ean_raw if _ean_valido(ean_raw) else None,
            codigo_ref=extrair_codigo_ref(descricao),
        ))

    return NFeParseResult(
        chave=chave,
        numero=_t(ide, "nNF"),
        serie=_t(ide, "serie"),
        data_emissao=_parse_date(data_raw),
        emit_cnpj=_t(emit, "CNPJ"),
        emit_nome=_t(emit, "xNome"),
        valor_total=valor_total,
        itens=itens,
    )
