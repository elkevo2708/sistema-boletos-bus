"""Catálogo de demostración. No consulta al SRI ni al Registro Civil.

Se usa solo cuando no hay URL de un proveedor contratado. Los números pasan
el dígito verificador ecuatoriano y los nombres son ficticios, salvo la cédula
de ejemplo que ya vive en clientes_facturacion.
"""

CATALOGO: dict[str, dict[str, str]] = {
    "1710034065": {
        "tipo": "cedula",
        "razon_social": "MARÍA CEDEÑO PAREDES",
        "direccion": "La Maná, Cotopaxi",
        "email": "maria.cedeno@gmail.com",
        "telefono": "0994127992",
    },
    "0926687856": {
        "tipo": "cedula",
        "razon_social": "JOSÉ ANDRADE MERA",
        "direccion": "Guayaquil, Guayas",
        "email": "jose.andrade@gmail.com",
        "telefono": "0991175522",
    },
    "0602813990": {
        "tipo": "cedula",
        "razon_social": "LUISA QUISHPE TIXI",
        "direccion": "Latacunga, Cotopaxi",
        "email": "luisa.quishpe@gmail.com",
        "telefono": "0980405468",
    },
    "1104680135": {
        "tipo": "cedula",
        "razon_social": "CARLOS RIVERA SALINAS",
        "direccion": "Loja",
        "email": "carlos.rivera@gmail.com",
        "telefono": "0990001104",
    },
    "1758439200": {
        "tipo": "cedula",
        "razon_social": "ANA BELTRÁN MOYA",
        "direccion": "Quito, Pichincha",
        "email": "ana.beltran@gmail.com",
        "telefono": "0990001758",
    },
    "1312567843": {
        "tipo": "cedula",
        "razon_social": "PEDRO ZAMBRANO CEDEÑO",
        "direccion": "Portoviejo, Manabí",
        "email": "pedro.zambrano@gmail.com",
        "telefono": "0990001312",
    },
    "1710034065001": {
        "tipo": "ruc",
        "razon_social": "MARÍA CEDEÑO PAREDES",
        "direccion": "La Maná, Cotopaxi",
        "email": "maria.cedeno@gmail.com",
        "telefono": "0994127992",
    },
    "0926687856001": {
        "tipo": "ruc",
        "razon_social": "JOSÉ ANDRADE MERA",
        "direccion": "Guayaquil, Guayas",
        "email": "jose.andrade@gmail.com",
        "telefono": "0991175522",
    },
}


def buscar_demo(identificacion: str) -> dict | None:
    return CATALOGO.get(identificacion)
