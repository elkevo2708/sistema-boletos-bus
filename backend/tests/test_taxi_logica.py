from datetime import datetime

from app.taxi_logica import es_nocturno, estimar_tarifa, haversine_km, mas_cercano


def test_tarifa_de_ejemplo_suma_arranque_km_y_minuto():
    precio = estimar_tarifa(2, 10, arranque=0.50, costo_km=0.45, costo_minuto=0.08, minima=1.25)
    assert precio == round(0.50 + 2 * 0.45 + 10 * 0.08, 2)


def test_tarifa_no_baja_de_la_minima_y_el_recargo_nocturno_suma():
    dia = estimar_tarifa(0.1, 1, arranque=0.10, costo_km=0.10, costo_minuto=0.01, minima=1.25)
    noche = estimar_tarifa(
        2, 10, arranque=1, costo_km=1, costo_minuto=0, minima=0.5, recargo_pct=15, nocturno=True
    )
    assert dia == 1.25
    assert noche == round((1 + 2) * 1.15, 2)


def test_la_noche_cruza_la_medianoche():
    desde = datetime(2026, 5, 19, 22, 0).time()
    hasta = datetime(2026, 5, 19, 6, 0).time()
    assert es_nocturno(datetime(2026, 5, 19, 23, 30), desde, hasta)
    assert es_nocturno(datetime(2026, 5, 20, 5, 0), desde, hasta)
    assert not es_nocturno(datetime(2026, 5, 19, 12, 0), desde, hasta)


def test_elige_al_disponible_mas_cercano():
    origen = (-0.94, -79.23)
    lejos = {"id": 2, "estado": "disponible", "lat": -0.90, "lng": -79.20}
    cerca = {"id": 1, "estado": "disponible", "lat": -0.9401, "lng": -79.2301}
    ocupado = {"id": 3, "estado": "ocupado", "lat": -0.94, "lng": -79.23}
    elegido = mas_cercano(origen, [lejos, ocupado, cerca])
    assert elegido["id"] == 1
    assert elegido["distancia_km"] < haversine_km(*origen, lejos["lat"], lejos["lng"])
