from app.ride import generar_ride


def test_ride_es_un_pdf():
    pdf = generar_ride(
        {
            "emisor_razon_social": "COOPERATIVA DE TRANSPORTE LA MANA",
            "emisor_ruc": "1790012344001",
            "emisor_direccion": "Matriz, La Maná, Cotopaxi",
            "numero": "001-001-000000001",
            "ambiente": "pruebas",
            "clave_acceso": "1" * 49,
            "numero_autorizacion": "1" * 49,
            "obligado_contabilidad": True,
            "razon_social_comprador": "MARÍA CEDEÑO PAREDES",
            "tipo_identificacion": "cedula",
            "identificacion_comprador": "1710034065",
            "direccion_comprador": "La Maná, Cotopaxi",
            "email_comprador": "maria.cedeno@gmail.com",
            "descripcion": "Pasaje La Maná - Quevedo",
            "ruta": "La Maná - Quevedo",
            "salida": "2026-10-17T06:30:00",
            "asiento": "4",
            "pasajero": "Ana Beltrán",
            "subtotal": "3.50",
            "iva": "0.00",
            "tarifa_iva": "0.00",
            "total": "3.50",
            "firma_omitida": True,
            "mensaje_sri": "Autorizado en modo de desarrollo, sin conexión al SRI.",
        }
    )
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 2000
