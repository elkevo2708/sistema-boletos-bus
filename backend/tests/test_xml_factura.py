from datetime import datetime
from decimal import Decimal

from app.clave_acceso import armar_clave_acceso, clave_valida
from app.impuestos import codigo_porcentaje_iva, desglosar_iva
from app.xml_factura import construir_xml


def test_pasaje_nacional_queda_con_iva_cero():
    base, iva = desglosar_iva("3.50", 0)
    assert base == Decimal("3.50")
    assert iva == Decimal("0.00")
    assert codigo_porcentaje_iva(0) == "0"


def test_tarifa_quince_se_descuenta_del_total_cobrado():
    base, iva = desglosar_iva("15.00", 15)
    assert base + iva == Decimal("15.00")
    assert iva > 0
    assert codigo_porcentaje_iva(15) == "4"
    assert codigo_porcentaje_iva(8) == "8"


def test_xml_factura_v110_incluye_clave_y_pasaje():
    fecha = datetime(2026, 10, 17, 6, 30)
    clave = armar_clave_acceso(fecha, "1790012344001", "pruebas", "001", "001", 1, 12345678)
    xml = construir_xml(
        {
            "ambiente": "pruebas",
            "emisor_razon_social": "COOPERATIVA DE TRANSPORTE LA MANA",
            "emisor_nombre_comercial": "TRANS LA MANA",
            "emisor_ruc": "1790012344001",
            "clave_acceso": clave,
            "establecimiento": "001",
            "punto_emision": "001",
            "secuencial": 1,
            "emisor_direccion": "Matriz, La Maná, Cotopaxi",
            "fecha_emision": fecha,
            "obligado_contabilidad": True,
            "tipo_identificacion": "cedula",
            "razon_social_comprador": "MARÍA CEDEÑO PAREDES",
            "identificacion_comprador": "1710034065",
            "direccion_comprador": "La Maná, Cotopaxi",
            "email_comprador": "maria.cedeno@gmail.com",
            "telefono_comprador": "0994127992",
            "subtotal": Decimal("3.50"),
            "total": Decimal("3.50"),
            "forma_pago": "19",
        },
        [
            {
                "codigo": "ABC123",
                "descripcion": "Pasaje La Maná - Quevedo. Salida 17/10/2026 06:30. Asiento 4. Pasajero Ana.",
                "cantidad": 1,
                "precio_unitario": Decimal("3.50"),
                "descuento": 0,
                "tarifa_iva": Decimal("0.00"),
                "base_imponible": Decimal("3.50"),
                "valor_iva": Decimal("0.00"),
                "ruta": "La Maná - Quevedo",
                "salida": "17/10/2026 06:30",
                "asiento": "4",
                "pasajero": "Ana Beltrán",
            }
        ],
    )
    assert 'version="1.1.0"' in xml
    assert "<codDoc>01</codDoc>" in xml
    assert "<tipoIdentificacionComprador>05</tipoIdentificacionComprador>" in xml
    assert "<codigoPorcentaje>0</codigoPorcentaje>" in xml
    assert "<tarifa>0.00</tarifa>" in xml
    assert "<importeTotal>3.50</importeTotal>" in xml
    assert "<formaPago>19</formaPago>" in xml
    assert f"<claveAcceso>{clave}</claveAcceso>" in xml
    assert clave_valida(clave)
    assert "Asiento 4" in xml
