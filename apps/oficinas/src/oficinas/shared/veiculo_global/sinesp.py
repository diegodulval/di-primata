"""
Cliente assíncrono para o SINESP Cidadão.

Reimplementa o protocolo do sinesp-client (reverse-engineering do app Android)
usando httpx para não introduzir conflito de dependências com urllib3/requests.

Referência: https://github.com/victor-torres/sinesp-client
"""
import math
import random
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha1
from hmac import new as hmac_new
from xml.etree import ElementTree

import httpx
import structlog

log = structlog.get_logger()

_URL = "https://cidadao.sinesp.gov.br/sinesp-cidadao/mobile/consultar-placa/v4"
_CAPTCHA_URL = "https://sinespcidadao.sinesp.gov.br/sinesp-cidadao/captchaMobile.png"
_SECRET = "#8.1.0#g8LzUadkEHs7mbRqbX5l"

_BODY_XML = (
    '<?xml version="1.0" encoding="utf-8" standalone="yes" ?>'
    '<v:Envelope xmlns:v="http://schemas.xmlsoap.org/soap/envelope/">'
    "<v:Header>"
    "<b>Samsung GT-I9192</b><c>ANDROID</c><d>8.1.0</d>"
    "<i>%s</i><e>4.1.5</e><f>10.0.0.1</f>"
    "<g>%s</g><k></k><h>%s</h><l>%s</l>"
    "<m>8797e74f0d6eb7b1ff3dc114d4aa12d3</m>"
    "</v:Header>"
    "<v:Body>"
    '<n0:getStatus xmlns:n0="http://soap.ws.placa.service.sinesp.serpro.gov.br/">'
    "<a>%s</a></n0:getStatus>"
    "</v:Body></v:Envelope>"
)

_HEADERS = {
    "Accept": "text/plain, */*; q=0.01",
    "Cache-Control": "no-cache",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Host": "sinespcidadao.sinesp.gov.br",
    "User-Agent": "SinespCidadao / 3.0.2.1 CFNetwork / 758.2.8 Darwin / 15.0.0",
    "Connection": "close",
}


@dataclass
class DadosSinesp:
    placa: str
    chassi: str | None
    marca: str | None
    modelo: str | None
    ano_fab: int | None
    ano_mod: int | None
    cor: str | None
    municipio: str | None
    uf: str | None
    situacao: str | None


def _token(plate: str) -> str:
    key = f"{plate}{_SECRET}".encode()
    return hmac_new(key, plate.encode(), sha1).hexdigest()


def _rand_coord(radius: float = 2000.0) -> float:
    seed = radius / 111000.0 * math.sqrt(random.random())
    return seed * math.sin(2 * 3.141592654 * random.random())


def _build_body(plate: str) -> bytes:
    lat = "%.7f" % (_rand_coord() - 38.5290245)
    lon = "%.7f" % (_rand_coord() - 3.7506985)
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return (_BODY_XML % (lat, _token(plate), lon, date, plate)).encode("utf-8")


def _parse(content: bytes) -> dict | None:
    body_tag = "{http://schemas.xmlsoap.org/soap/envelope/}Body"
    resp_tag = "{http://soap.ws.placa.service.sinesp.serpro.gov.br/}getStatusResponse"
    try:
        xml = content.decode("latin-1").encode("utf-8")
        root = ElementTree.fromstring(xml)
        els = root.find(body_tag).find(resp_tag).find("return")  # type: ignore[union-attr]
        data = {el.tag: el.text for el in els}  # type: ignore[union-attr]
    except Exception:
        return None

    if data.get("codigoRetorno") != "0":
        return None

    return data


def _int_or_none(v: str | None) -> int | None:
    try:
        return int(v) if v else None
    except ValueError:
        return None


async def consultar_placa(placa: str, timeout: float = 10.0) -> DadosSinesp | None:
    """
    Consulta o SINESP Cidadão de forma assíncrona.
    Retorna None se a placa não for encontrada ou se a requisição falhar.
    Nunca lança exceção — falha silenciosa para não bloquear o fluxo de cadastro.

    O SINESP bloqueia IPs fora do Brasil. Configure SINESP_PROXY_URL no .env
    para usar um proxy SOCKS5 (ex: socks5://user:pass@host:1080).
    """
    from oficinas.core.config import settings

    proxy = settings.sinesp_proxy_url
    try:
        async with httpx.AsyncClient(
            verify=False,
            timeout=timeout,
            proxy=proxy,  # None = sem proxy; str = SOCKS5/HTTP
        ) as client:
            cookie_resp = await client.get(_CAPTCHA_URL)
            jsessionid = cookie_resp.cookies.get("JSESSIONID")

            resp = await client.post(
                _URL,
                content=_build_body(placa),
                headers=_HEADERS,
                cookies={"JSESSIONID": jsessionid} if jsessionid else {},
            )

        data = _parse(resp.content)
        if not data:
            log.info("sinesp_nao_encontrado", placa=placa)
            return None

        return DadosSinesp(
            placa=placa,
            chassi=data.get("chassi") or None,
            marca=data.get("marca") or None,
            modelo=data.get("modelo") or None,
            ano_fab=_int_or_none(data.get("ano")),
            ano_mod=_int_or_none(data.get("anoModelo")),
            cor=data.get("cor") or None,
            municipio=data.get("municipio") or None,
            uf=data.get("uf") or None,
            situacao=data.get("situacao") or None,
        )
    except Exception as exc:
        log.warning("sinesp_consulta_falhou", placa=placa, erro=str(exc))
        return None
