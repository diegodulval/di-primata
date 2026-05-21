import uuid
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from oficinas.modules.estoque.models import Fornecedor, Produto

_XML_FIXTURE = b"""<?xml version="1.0" encoding="UTF-8"?>
<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe">
  <NFe>
    <infNFe Id="NFe35231212345678000195550010000001231000000001">
      <ide>
        <nNF>123</nNF>
        <serie>1</serie>
        <dhEmi>2023-12-01T10:00:00-03:00</dhEmi>
      </ide>
      <emit>
        <CNPJ>12345678000195</CNPJ>
        <xNome>Distribuidora de Pecas LTDA</xNome>
      </emit>
      <det nItem="1">
        <prod>
          <cProd>FLT001</cProd>
          <xProd>FILTRO DE OLEO MANN</xProd>
          <NCM>84212300</NCM>
          <qCom>10.000</qCom>
          <vUnCom>25.50</vUnCom>
        </prod>
        <imposto>
          <ICMS><ICMS00><pICMS>12.00</pICMS></ICMS00></ICMS>
        </imposto>
      </det>
      <total><ICMSTot><vNF>255.00</vNF></ICMSTot></total>
    </infNFe>
  </NFe>
</nfeProc>"""


@pytest.fixture
def xml_fixture() -> bytes:
    return _XML_FIXTURE


@pytest.fixture
def tenant_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def produto(tenant_id) -> Produto:
    return Produto(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        codigo="FLT001",
        descricao="FILTRO DE OLEO MANN",
        ncm="84212300",
        marca=None,
        localizacao=None,
        preco_custo=Decimal("25.50"),
        preco_venda=Decimal("35.00"),
        estoque_atual=Decimal("5.000"),
        estoque_minimo=Decimal("0"),
        estoque_maximo=Decimal("0"),
        ativo=True,
    )


@pytest.fixture
def fornecedor(tenant_id) -> Fornecedor:
    return Fornecedor(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        razao_social="Distribuidora de Pecas LTDA",
        cnpj="12345678000195",
        contato=None,
    )


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.add = MagicMock()
    vazio = MagicMock()
    vazio.scalar_one_or_none.return_value = None
    vazio.scalars.return_value.all.return_value = []
    db.execute.return_value = vazio
    return db


def resultado_com(obj):
    r = MagicMock()
    r.scalar_one_or_none.return_value = obj
    return r


def resultado_lista(items: list):
    r = MagicMock()
    r.scalars.return_value.all.return_value = items
    return r


def resultado_vazio():
    r = MagicMock()
    r.scalar_one_or_none.return_value = None
    return r
