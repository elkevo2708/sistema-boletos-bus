from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID

from app.firma import FirmadorOmitido, FirmadorXadesBes


def test_sin_certificado_la_firma_se_omite():
    resultado = FirmadorOmitido().firmar("<factura/>")
    assert resultado.omitida is True
    assert resultado.xml == "<factura/>"


def test_xades_bes_con_p12(tmp_path: Path):
    llave = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    nombre = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "La Mana Pruebas")])
    ahora = datetime.now(timezone.utc)
    certificado = (
        x509.CertificateBuilder()
        .subject_name(nombre)
        .issuer_name(nombre)
        .public_key(llave.public_key())
        .serial_number(1)
        .not_valid_before(ahora - timedelta(minutes=1))
        .not_valid_after(ahora + timedelta(days=2))
        .sign(llave, hashes.SHA256())
    )
    ruta = tmp_path / "emisor.p12"
    ruta.write_bytes(
        pkcs12.serialize_key_and_certificates(
            b"emisor",
            llave,
            certificado,
            None,
            serialization.BestAvailableEncryption(b"clave-prueba"),
        )
    )
    xml = '<factura id="comprobante" version="1.1.0"><infoTributaria><ruc>1790012344001</ruc></infoTributaria></factura>'
    firmado = FirmadorXadesBes(str(ruta), "clave-prueba").firmar(xml)
    assert firmado.omitida is False
    assert "Signature" in firmado.xml
    assert "QualifyingProperties" in firmado.xml or "xades" in firmado.xml.lower()
    assert "1790012344001" in firmado.xml
