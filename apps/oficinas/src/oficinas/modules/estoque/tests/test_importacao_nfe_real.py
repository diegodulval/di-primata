"""
Testes de importação usando a NF-e real:
  31260545987005028360550010003538181116087337.xml

Emitente : COMERCIAL AUTOMOTIVA S.A. — CNPJ 45987005028360
  Item 1 : cProd 93031   "KIT AMORT TRAS E/D 1 BT/CF/CX"    qty=2  R$115,44  EAN 7891579313171
  Item 2 : cProd 3327591 "AMORTECEDOR TRASEIRO ESQ/DIR"       qty=2  R$177,66  EAN 7899027348942

Nenhum item tem código de referência numérico na descrição (ambos começam com palavras).
O matching automático só ocorre via EAN ou via mapeamento aprendido.
"""
import uuid
from datetime import date
from decimal import Decimal
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from oficinas.core.enums import StatusItem
from oficinas.core.exceptions import NFeJaImportada
from oficinas.modules.estoque.models import (
    EntradaNfe,
    Fornecedor,
    MapeamentoFornecedorProduto,
    Produto,
)
from oficinas.modules.estoque.parser import extrair_codigo_ref, parse_nfe
from oficinas.modules.estoque.rascunho_service import RascunhoService
from oficinas.modules.estoque.tests.conftest import resultado_com, resultado_lista, resultado_vazio

# ── Fixture da NF-e real ───────────────────────────────────────────────────────

_CHAVE   = "31260545987005028360550010003538181116087337"
_NFE_XML = (
    Path(__file__).parent
    / "fixtures" / "nfxml"
    / f"{_CHAVE}.xml"
).read_bytes()

# ── Valores esperados (derivados do XML) ───────────────────────────────────────

EMIT_CNPJ   = "45987005028360"
EMIT_NOME   = "COMERCIAL AUTOMOTIVA S.A."
NF_NUMERO   = "353818"
NF_DATA     = date(2026, 5, 21)
VALOR_TOTAL = Decimal("586.20")

# Item 1
I1_CPROD = "93031"
I1_DESC  = "KIT AMORT TRAS E/D 1 BT/CF/CX"
I1_NCM   = "87089990"
I1_QTD   = Decimal("2.0000")
I1_PRECO = Decimal("115.44")
I1_EAN   = "7891579313171"

# Item 2
I2_CPROD = "3327591"
I2_DESC  = "AMORTECEDOR TRASEIRO ESQ/DIR"
I2_NCM   = "87088000"
I2_QTD   = Decimal("2.0000")
I2_PRECO = Decimal("177.66")
I2_EAN   = "7899027348942"


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def tenant_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.add = MagicMock()
    vazio = MagicMock()
    vazio.scalar_one_or_none.return_value = None
    vazio.scalars.return_value.all.return_value = []
    db.execute.return_value = vazio
    return db


def _fornecedor(tenant_id: uuid.UUID) -> Fornecedor:
    return Fornecedor(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        razao_social=EMIT_NOME,
        cnpj=EMIT_CNPJ,
    )


def _produto_ean(tenant_id: uuid.UUID, ean: str, codigo: str) -> Produto:
    return Produto(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        codigo=codigo,
        descricao="Produto de teste",
        ncm=None,
        preco_custo=Decimal("0"),
        preco_venda=Decimal("0"),
        estoque_atual=Decimal("0"),
        estoque_minimo=Decimal("0"),
        estoque_maximo=Decimal("0"),
        ativo=True,
        ean=ean,
    )


def _mapeamento(tenant_id: uuid.UUID, fornecedor_id: uuid.UUID,
                codigo_fornecedor: str, produto_id: uuid.UUID) -> MapeamentoFornecedorProduto:
    return MapeamentoFornecedorProduto(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        fornecedor_id=fornecedor_id,
        codigo_fornecedor=codigo_fornecedor,
        produto_id=produto_id,
    )


# ── Parser — campos da NF-e real ───────────────────────────────────────────────

def test_parser_chave():
    r = parse_nfe(_NFE_XML)
    assert r.chave == _CHAVE


def test_parser_emitente():
    r = parse_nfe(_NFE_XML)
    assert r.emit_cnpj == EMIT_CNPJ
    assert r.emit_nome == EMIT_NOME


def test_parser_numero_serie_data():
    r = parse_nfe(_NFE_XML)
    assert r.numero == NF_NUMERO
    assert r.serie == "1"
    assert r.data_emissao == NF_DATA


def test_parser_valor_total():
    r = parse_nfe(_NFE_XML)
    assert r.valor_total == VALOR_TOTAL


def test_parser_dois_itens():
    r = parse_nfe(_NFE_XML)
    assert len(r.itens) == 2


def test_parser_item1_campos():
    r = parse_nfe(_NFE_XML)
    item = r.itens[0]
    assert item.codigo    == I1_CPROD
    assert item.descricao == I1_DESC
    assert item.ncm       == I1_NCM
    assert item.quantidade    == I1_QTD
    assert item.preco_unitario == I1_PRECO
    assert item.ean       == I1_EAN


def test_parser_item2_campos():
    r = parse_nfe(_NFE_XML)
    item = r.itens[1]
    assert item.codigo    == I2_CPROD
    assert item.descricao == I2_DESC
    assert item.ncm       == I2_NCM
    assert item.quantidade    == I2_QTD
    assert item.preco_unitario == I2_PRECO
    assert item.ean       == I2_EAN


def test_parser_eans_validos():
    """Ambos os EANs (13 dígitos) devem ser reconhecidos como válidos."""
    r = parse_nfe(_NFE_XML)
    assert r.itens[0].ean == I1_EAN
    assert r.itens[1].ean == I2_EAN


def test_parser_codigo_ref_nulo_ambos_itens():
    """Descrições que começam com palavras sem dígito não geram código de referência."""
    assert extrair_codigo_ref(I1_DESC) is None   # "KIT …"
    assert extrair_codigo_ref(I2_DESC) is None   # "AMORTECEDOR …"

    r = parse_nfe(_NFE_XML)
    assert r.itens[0].codigo_ref is None
    assert r.itens[1].codigo_ref is None


# ── RascunhoService — cenários de importação ───────────────────────────────────

async def test_importar_nfe_real_sem_matches_dois_pendentes(mock_db, tenant_id):
    """Sem produtos cadastrados nem mapeamentos: ambos os itens ficam PENDENTE."""
    # EntradaNfe check, Fornecedor check (cria novo — id=None → sem mapeamento),
    # EAN item1, EAN item2
    mock_db.execute.side_effect = [
        resultado_vazio(),   # EntradaNfe
        resultado_vazio(),   # Fornecedor → cria novo
        resultado_vazio(),   # EAN item 1
        resultado_vazio(),   # EAN item 2
    ]

    rascunho, itens = await RascunhoService(mock_db).criar_rascunho(_NFE_XML, tenant_id)

    assert len(itens) == 2
    assert itens[0].status_item == StatusItem.PENDENTE
    assert itens[1].status_item == StatusItem.PENDENTE
    assert itens[0].codigo_fornecedor == I1_CPROD
    assert itens[1].codigo_fornecedor == I2_CPROD


async def test_importar_nfe_real_vincula_por_ean_item1(mock_db, tenant_id):
    """Item 1 tem EAN cadastrado → AUTO_VINCULADO; item 2 sem match → PENDENTE."""
    produto1 = _produto_ean(tenant_id, I1_EAN, "EST001")

    mock_db.execute.side_effect = [
        resultado_vazio(),          # EntradaNfe
        resultado_vazio(),          # Fornecedor → cria novo
        resultado_com(produto1),    # EAN item 1 → match
        resultado_vazio(),          # EAN item 2 → sem match
    ]

    rascunho, itens = await RascunhoService(mock_db).criar_rascunho(_NFE_XML, tenant_id)

    assert itens[0].status_item == StatusItem.AUTO_VINCULADO
    assert itens[0].produto_id  == produto1.id
    assert itens[1].status_item == StatusItem.PENDENTE


async def test_importar_nfe_real_vincula_por_ean_ambos(mock_db, tenant_id):
    """Ambos os EANs encontrados → ambos AUTO_VINCULADO."""
    produto1 = _produto_ean(tenant_id, I1_EAN, "EST001")
    produto2 = _produto_ean(tenant_id, I2_EAN, "EST002")

    mock_db.execute.side_effect = [
        resultado_vazio(),          # EntradaNfe
        resultado_vazio(),          # Fornecedor → cria novo
        resultado_com(produto1),    # EAN item 1
        resultado_com(produto2),    # EAN item 2
    ]

    rascunho, itens = await RascunhoService(mock_db).criar_rascunho(_NFE_XML, tenant_id)

    assert itens[0].status_item == StatusItem.AUTO_VINCULADO
    assert itens[1].status_item == StatusItem.AUTO_VINCULADO


async def test_importar_nfe_real_vincula_por_mapeamento_aprendido(mock_db, tenant_id):
    """Fornecedor já cadastrado + mapeamento aprendido → AUTO_VINCULADO sem precisar de EAN."""
    fornecedor = _fornecedor(tenant_id)
    produto1   = _produto_ean(tenant_id, I1_EAN, "EST001")
    produto2   = _produto_ean(tenant_id, I2_EAN, "EST002")
    mapa1 = _mapeamento(tenant_id, fornecedor.id, I1_CPROD, produto1.id)
    mapa2 = _mapeamento(tenant_id, fornecedor.id, I2_CPROD, produto2.id)

    mock_db.execute.side_effect = [
        resultado_vazio(),          # EntradaNfe
        resultado_com(fornecedor),  # Fornecedor → encontrado (id definido)
        resultado_com(mapa1),       # Mapeamento item 1 → match
        resultado_com(mapa2),       # Mapeamento item 2 → match
    ]

    rascunho, itens = await RascunhoService(mock_db).criar_rascunho(_NFE_XML, tenant_id)

    assert itens[0].status_item == StatusItem.AUTO_VINCULADO
    assert itens[0].produto_id  == produto1.id
    assert itens[1].status_item == StatusItem.AUTO_VINCULADO
    assert itens[1].produto_id  == produto2.id


async def test_importar_nfe_real_mapeamento_item1_ean_item2(mock_db, tenant_id):
    """Mapeamento só para item 1; item 2 usa EAN como fallback."""
    fornecedor = _fornecedor(tenant_id)
    produto1   = _produto_ean(tenant_id, I1_EAN, "EST001")
    produto2   = _produto_ean(tenant_id, I2_EAN, "EST002")
    mapa1 = _mapeamento(tenant_id, fornecedor.id, I1_CPROD, produto1.id)

    mock_db.execute.side_effect = [
        resultado_vazio(),          # EntradaNfe
        resultado_com(fornecedor),  # Fornecedor → encontrado
        resultado_com(mapa1),       # Mapeamento item 1 → match
        resultado_vazio(),          # Mapeamento item 2 → sem match
        resultado_com(produto2),    # EAN item 2 → match
    ]

    rascunho, itens = await RascunhoService(mock_db).criar_rascunho(_NFE_XML, tenant_id)

    assert itens[0].status_item == StatusItem.AUTO_VINCULADO
    assert itens[1].status_item == StatusItem.AUTO_VINCULADO


async def test_importar_nfe_real_chave_ja_importada(mock_db, tenant_id):
    """Segunda importação da mesma NF-e levanta NFeJaImportada."""
    entrada_existente = EntradaNfe(id=uuid.uuid4(), tenant_id=tenant_id)
    mock_db.execute.return_value = resultado_com(entrada_existente)

    with pytest.raises(NFeJaImportada):
        await RascunhoService(mock_db).criar_rascunho(_NFE_XML, tenant_id)


async def test_importar_nfe_real_fornecedor_upsert_cnpj_e_nome(mock_db, tenant_id):
    """O fornecedor criado usa o CNPJ e nome exatos do emitente da NF-e."""
    mock_db.execute.side_effect = [
        resultado_vazio(),  # EntradaNfe
        resultado_vazio(),  # Fornecedor → cria novo
        resultado_vazio(),  # EAN item 1
        resultado_vazio(),  # EAN item 2
    ]

    await RascunhoService(mock_db).criar_rascunho(_NFE_XML, tenant_id)

    objetos_adicionados = [call.args[0] for call in mock_db.add.call_args_list]
    fornecedores = [o for o in objetos_adicionados if isinstance(o, Fornecedor)]
    assert len(fornecedores) == 1
    assert fornecedores[0].cnpj        == EMIT_CNPJ
    assert fornecedores[0].razao_social == EMIT_NOME


async def test_importar_nfe_real_rascunho_campos_corretos(mock_db, tenant_id):
    """Rascunho criado carrega número, data e valor total da NF-e."""
    mock_db.execute.side_effect = [
        resultado_vazio(),  # EntradaNfe
        resultado_vazio(),  # Fornecedor
        resultado_vazio(),  # EAN item 1
        resultado_vazio(),  # EAN item 2
    ]

    rascunho, _ = await RascunhoService(mock_db).criar_rascunho(_NFE_XML, tenant_id)

    assert rascunho.numero_nf    == NF_NUMERO
    assert rascunho.data_emissao == NF_DATA
    assert rascunho.valor_total  == VALOR_TOTAL
    assert rascunho.chave_nfe    == _CHAVE


async def test_importar_nfe_real_itens_preservam_ean_e_ncm(mock_db, tenant_id):
    """EAN e NCM de cada item são preservados no rascunho para matching futuro."""
    mock_db.execute.side_effect = [
        resultado_vazio(),
        resultado_vazio(),
        resultado_vazio(),
        resultado_vazio(),
    ]

    _, itens = await RascunhoService(mock_db).criar_rascunho(_NFE_XML, tenant_id)

    assert itens[0].ean == I1_EAN
    assert itens[0].ncm == I1_NCM
    assert itens[1].ean == I2_EAN
    assert itens[1].ncm == I2_NCM
