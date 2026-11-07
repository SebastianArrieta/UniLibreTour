"""Límite de intentos fallidos en memoria (ventana deslizante, por proceso).

Solo cuentan los FALLOS (contraseña o código incorrectos): los accesos
correctos nunca bloquean a nadie, aunque muchos usuarios compartan IP (por
ejemplo, detrás del proxy TLS o la red de la universidad).

Con varios workers de gunicorn cada uno lleva su cuenta, así que el límite
efectivo es ``maximo × workers``. Suficiente para frenar fuerza bruta sin
dependencias externas.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock

_fallos: dict[str, deque] = defaultdict(deque)
_lock = Lock()


def _purgar(cola: deque, ahora: float, ventana_seg: int) -> None:
    while cola and ahora - cola[0] > ventana_seg:
        cola.popleft()


def bloqueado(clave: str, maximo: int, ventana_seg: int) -> bool:
    """¿La clave acumula ``maximo`` fallos o más dentro de la ventana?"""
    ahora = time.monotonic()
    with _lock:
        cola = _fallos.get(clave)
        if not cola:
            return False
        _purgar(cola, ahora, ventana_seg)
        return len(cola) >= maximo


def registrar_fallo(clave: str) -> None:
    ahora = time.monotonic()
    with _lock:
        _fallos[clave].append(ahora)
        if len(_fallos) > 10000:  # evita crecimiento sin límite
            for k in [k for k, v in _fallos.items() if not v or ahora - v[-1] > 3600]:
                del _fallos[k]


def limpiar(clave: str) -> None:
    with _lock:
        _fallos.pop(clave, None)
