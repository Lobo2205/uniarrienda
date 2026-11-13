"""Puerto para la pasarela de pagos. El negocio no sabe que por detrás es Stripe."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class SesionPago:
    """Lo que la pasarela necesita devolver para que el estudiante pague."""
    referencia: str   # id de la sesión en la pasarela
    url_pago: str     # URL donde el estudiante completa el pago


@dataclass
class ResultadoWebhook:
    """Lo que el webhook de la pasarela nos informa cuando el estudiante termina."""
    referencia: str
    aprobado: bool


class PasarelaPagos(ABC):
    @abstractmethod
    def crear_sesion(self, monto: int, moneda: str, descripcion: str, metadata: dict) -> SesionPago: ...

    @abstractmethod
    def leer_evento(self, cuerpo: bytes, firma: str) -> Optional[ResultadoWebhook]:
        """Verifica la firma del webhook y devuelve el resultado, o None si no nos interesa."""
