from datetime import datetime

from app.clave_acceso import armar_clave_acceso, clave_valida, digito_modulo11


def test_modulo_11_de_ejemplo_corto():
    assert digito_modulo11("12345678") == "5"


def test_clave_de_acceso_tiene_49_digitos_y_verificador():
    clave = armar_clave_acceso(
        datetime(2026, 10, 17, 6, 30),
        "1790012344001",
        "pruebas",
        "001",
        "001",
        1,
        12345678,
    )
    assert len(clave) == 49
    assert clave.startswith("17102026")
    assert clave[8:10] == "01"
    assert "1790012344001" in clave
    assert clave_valida(clave)
    assert not clave_valida(clave[:-1] + ("0" if clave[-1] != "0" else "1"))
    assert not clave_valida("1" * 48)
