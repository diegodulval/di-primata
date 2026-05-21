"""
Parser de XML NF-e (versão 4.00).
Retorna estruturas de dados simples — sem dependência de banco ou ORM.
"""
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation

_NS = "http://www.portalfiscal.inf.br/nfe"


def _t(elem, tag: str, default: str = "") -> str:
    """Retorna o texto do primeiro filho com `tag`, ou `default`."""
    found = elem.find(f"{{{_NS}}}{tag}")
    return (found.text or default) if found is not None else default


def _d(valor: str) -> Decimal:
    """Converte string para Decimal, retorna 0 em caso de falha."""
    try:
        return Decimal(valor)
    except (InvalidOperation, TypeError):
        return Decimal("0")


@dataclass
class ItemNFe:
    codigo:         str
    descricao:      str
    ncm:            str
    quantidade:     Decimal
    preco_unitario: Decimal
    icms:           Decimal = Decimal("0")
    ipi:            Decimal = Decimal("0")


@dataclass
class NFeParseResult:
    chave:       str
    numero:      str
    serie:       str
    data_emissao: str          # ISO 8601 completo do XML
    emit_cnpj:   str
    emit_nome:   str
    valor_total: Decimal
    itens:       list[ItemNFe] = field(default_factory=list)


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

        itens.append(ItemNFe(
            codigo=_t(prod, "cProd"),
            descricao=_t(prod, "xProd"),
            ncm=_t(prod, "NCM"),
            quantidade=_d(_t(prod, "qCom")),
            preco_unitario=_d(_t(prod, "vUnCom")),
            icms=_d(icms_elem.text) if icms_elem is not None else Decimal("0"),
            ipi=_d(ipi_elem.text)  if ipi_elem  is not None else Decimal("0"),
        ))

    return NFeParseResult(
        chave=chave,
        numero=_t(ide, "nNF"),
        serie=_t(ide, "serie"),
        data_emissao=data_raw,
        emit_cnpj=_t(emit, "CNPJ"),
        emit_nome=_t(emit, "xNome"),
        valor_total=valor_total,
        itens=itens,
    )
