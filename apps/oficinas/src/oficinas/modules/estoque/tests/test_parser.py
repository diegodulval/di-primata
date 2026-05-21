from decimal import Decimal

import pytest

from oficinas.modules.estoque.parser import parse_nfe


_XML_DOIS_ITENS = b"""<?xml version="1.0" encoding="UTF-8"?>
<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe">
  <NFe>
    <infNFe Id="NFe35231212345678000195550010000001231000000002">
      <ide><nNF>456</nNF><serie>2</serie><dhEmi>2023-06-15T08:00:00-03:00</dhEmi></ide>
      <emit>
        <CNPJ>98765432000111</CNPJ>
        <xNome>Fornecedor Dois LTDA</xNome>
      </emit>
      <det nItem="1">
        <prod>
          <cProd>P001</cProd><xProd>FILTRO AR</xProd><NCM>84213990</NCM>
          <qCom>5.000</qCom><vUnCom>12.00</vUnCom>
        </prod>
        <imposto>
          <ICMS><ICMS20><pICMS>18.00</pICMS></ICMS20></ICMS>
          <IPI><IPITrib><pIPI>5.00</pIPI></IPITrib></IPI>
        </imposto>
      </det>
      <det nItem="2">
        <prod>
          <cProd>P002</cProd><xProd>VELA DE IGNICAO</xProd><NCM>85111000</NCM>
          <qCom>4.000</qCom><vUnCom>8.50</vUnCom>
        </prod>
        <imposto><ICMS><ICMS00><pICMS>12.00</pICMS></ICMS00></ICMS></imposto>
      </det>
      <total><ICMSTot><vNF>94.00</vNF></ICMSTot></total>
    </infNFe>
  </NFe>
</nfeProc>"""


def test_parse_chave_numero_serie(xml_fixture):
    r = parse_nfe(xml_fixture)
    assert r.chave == "35231212345678000195550010000001231000000001"
    assert r.numero == "123"
    assert r.serie == "1"


def test_parse_emitente(xml_fixture):
    r = parse_nfe(xml_fixture)
    assert r.emit_cnpj == "12345678000195"
    assert r.emit_nome == "Distribuidora de Pecas LTDA"


def test_parse_valor_total(xml_fixture):
    r = parse_nfe(xml_fixture)
    assert r.valor_total == Decimal("255.00")


def test_parse_item_unico(xml_fixture):
    r = parse_nfe(xml_fixture)
    assert len(r.itens) == 1
    item = r.itens[0]
    assert item.codigo == "FLT001"
    assert item.descricao == "FILTRO DE OLEO MANN"
    assert item.ncm == "84212300"
    assert item.quantidade == Decimal("10.000")
    assert item.preco_unitario == Decimal("25.50")
    assert item.icms == Decimal("12.00")
    assert item.ipi == Decimal("0")  # sem IPI no XML


def test_parse_dois_itens_e_ipi():
    r = parse_nfe(_XML_DOIS_ITENS)
    assert len(r.itens) == 2
    assert r.itens[0].ipi == Decimal("5.00")
    assert r.itens[1].ipi == Decimal("0")  # sem IPI


def test_parse_data_emissao(xml_fixture):
    r = parse_nfe(xml_fixture)
    assert "2023-12-01" in r.data_emissao


def test_parse_xml_invalido_levanta_value_error():
    with pytest.raises(ValueError, match="XML inválido"):
        parse_nfe(b"isso nao e xml")


def test_parse_xml_sem_infnfe_levanta_value_error():
    xml = b"""<?xml version="1.0"?><root xmlns="http://www.portalfiscal.inf.br/nfe"><vazio/></root>"""
    with pytest.raises(ValueError, match="infNFe"):
        parse_nfe(xml)
