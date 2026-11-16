"""Contratos de pasarela y catálogo demo, sin red ni base de datos."""

from decimal import Decimal

from app.consulta_identificacion import armar_nombre, extraer
from app.demo_cedulas import CATALOGO
from app.identificacion import cedula_valida, ruc_valido
from app.pagos import centavos, cuerpo_payphone, deuna_aprobado, firmar, firma_valida, payphone_aprobado
from app.xml_factura import forma_pago


def test_payphone_prepara_centavos_sin_iva():
    from app.pagos import SolicitudPago

    cuerpo = cuerpo_payphone(
        SolicitudPago("ABC", Decimal("3.50"), "PAY-12345678", "payphone"),
        "https://boletos.example/api/pagos/payphone/retorno",
    )
    assert cuerpo["amount"] == 350
    assert cuerpo["amountWithoutTax"] == 350
    assert cuerpo["tax"] == 0
    assert cuerpo["currency"] == "USD"
    assert cuerpo["timeZone"] == -5
    assert cuerpo["clientTransactionId"] == "PAY-12345678"


def test_confirmacion_payphone_exige_el_monto():
    assert payphone_aprobado({"statusCode": 3, "transactionStatus": "Approved", "amount": 350}, Decimal("3.50"))
    assert not payphone_aprobado({"statusCode": 3, "transactionStatus": "Approved", "amount": 100}, Decimal("3.50"))
    assert not payphone_aprobado({"statusCode": 2, "transactionStatus": "Canceled", "amount": 350}, Decimal("3.50"))


def test_deuna_lee_el_estado_anidado():
    datos = {"order": {"order_id": "DUNA-1", "payment": {"data": {"status": "succeeded"}}}}
    assert deuna_aprobado(datos)
    assert not deuna_aprobado({"order": {"payment": {"data": {"status": "pending"}}}})


def test_firma_hmac_no_acepta_otra_clave():
    cuerpo = b'{"status":"approved"}'
    firma = firmar(cuerpo, "lamana-sandbox-firma")
    assert firma_valida(cuerpo, firma, "lamana-sandbox-firma")
    assert not firma_valida(cuerpo, firma, "otra")
    assert not firma_valida(cuerpo + b" ", firma, "lamana-sandbox-firma")


def test_formas_de_pago_sri():
    assert forma_pago("tarjeta") == "19"
    assert forma_pago("payphone") == "20"
    assert forma_pago("deuna") == "17"
    assert centavos(Decimal("14.00")) == 1400


def test_catalogo_demo_son_identificaciones_validas():
    assert len(CATALOGO) >= 6
    for numero, ficha in CATALOGO.items():
        if ficha["tipo"] == "cedula":
            assert cedula_valida(numero), numero
        else:
            assert ruc_valido(numero), numero
        assert ficha["razon_social"]


def test_mapeo_de_campos_json():
    datos = {"data": {"nombreCompleto": "ANA BELTRÁN"}, "direccion": "Quito"}
    assert extraer(datos, "data.nombreCompleto") == "ANA BELTRÁN"
    assert extraer(datos, "direccion") == "Quito"
    assert armar_nombre({"nombres": "JOSÉ", "apellidos": "ANDRADE"}) == "JOSÉ ANDRADE"
