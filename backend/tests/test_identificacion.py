from app.identificacion import (
    cedula_valida,
    clasificar_ruc,
    ruc_valido,
    validar_identificacion,
)


def test_cedula_modulo_10():
    assert cedula_valida("1710034065")
    assert not cedula_valida("1710034066")
    assert not cedula_valida("171003406")
    assert not cedula_valida("0010034065")
    assert not cedula_valida("1760034065")
    assert cedula_valida("3010034068")
    assert not cedula_valida("3010034065")
    assert validar_identificacion("cedula", "1710034065") is None
    assert validar_identificacion("cedula", "1710034066") is not None


def test_ruc_natural_privado_y_publico():
    assert ruc_valido("1710034065001")
    assert clasificar_ruc("1710034065001") == "natural"
    assert not ruc_valido("1710034065000")

    assert ruc_valido("1790012344001")
    assert clasificar_ruc("1790012344001") == "privado"
    assert not ruc_valido("1790012345001")

    assert ruc_valido("1760001200001")
    assert clasificar_ruc("1760001200001") == "publico"
    assert not ruc_valido("1760001200000")


def test_pasaporte_y_consumidor_final():
    assert validar_identificacion("pasaporte", "AB123456") is None
    assert validar_identificacion("pasaporte", "A1") is not None
    assert validar_identificacion("consumidor_final", "9999999999999") is None
    assert validar_identificacion("consumidor_final", "1710034065") is not None
