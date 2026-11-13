"""Adaptador de salida para Stripe. Y un adaptador falso para pruebas y desarrollo sin internet."""
import json
from typing import Optional

from app.puertos.pasarela import PasarelaPagos, ResultadoWebhook, SesionPago


class PasarelaStripe(PasarelaPagos):
    """Cumple PasarelaPagos usando Stripe Checkout en modo de prueba."""

    def __init__(self, clave_secreta: str, secreto_webhook: str, url_exito: str, url_cancelar: str):
        import stripe  # importación perezosa: solo si realmente se usa Stripe
        stripe.api_key = clave_secreta
        self._stripe = stripe
        self.secreto_webhook = secreto_webhook
        self.url_exito = url_exito
        self.url_cancelar = url_cancelar

    def crear_sesion(self, monto: int, moneda: str, descripcion: str, metadata: dict) -> SesionPago:
        sesion = self._stripe.checkout.Session.create(
            mode="payment",
            line_items=[{
                "price_data": {
                    "currency": moneda,
                    "product_data": {"name": descripcion},
                    "unit_amount": monto,  # COP usa unidad mínima = 1 peso (sin decimales)
                },
                "quantity": 1,
            }],
            success_url=self.url_exito,
            cancel_url=self.url_cancelar,
            metadata={k: str(v) for k, v in metadata.items()},
        )
        return SesionPago(referencia=sesion.id, url_pago=sesion.url)

    def obtener_url(self, referencia: str) -> Optional[str]:
        try:
            sesion = self._stripe.checkout.Session.retrieve(referencia)
        except Exception:
            return None
        return sesion.url if sesion.status == "open" else None

    def leer_evento(self, cuerpo: bytes, firma: str) -> Optional[ResultadoWebhook]:
        try:
            evento = self._stripe.Webhook.construct_event(cuerpo, firma, self.secreto_webhook)
        except Exception:
            return None
        tipo = evento.get("type")
        objeto = evento["data"]["object"]
        referencia = objeto.get("id")
        if tipo == "checkout.session.completed" and objeto.get("payment_status") == "paid":
            return ResultadoWebhook(referencia=referencia, aprobado=True)
        if tipo in ("checkout.session.expired", "checkout.session.async_payment_failed"):
            return ResultadoWebhook(referencia=referencia, aprobado=False)
        return None


class PasarelaFalsa(PasarelaPagos):
    """Pasarela de desarrollo y pruebas: no necesita cuenta de Stripe.

    Si en el .env no configuras STRIPE_SECRET_KEY, se usa esta. El estudiante "paga"
    entrando a la URL que devuelve, y el pago se da por aprobado automáticamente.
    """

    def __init__(self, url_base: str):
        self.url_base = url_base.rstrip("/")
        self._contador = 0

    def crear_sesion(self, monto: int, moneda: str, descripcion: str, metadata: dict) -> SesionPago:
        self._contador += 1
        ref = f"fake_{self._contador}_{metadata.get('id_pago', 0)}"
        url = f"{self.url_base}/pagos/falso/confirmar?referencia={ref}"
        return SesionPago(referencia=ref, url_pago=url)

    def obtener_url(self, referencia: str) -> Optional[str]:
        return f"{self.url_base}/pagos/falso/confirmar?referencia={referencia}"

    def leer_evento(self, cuerpo: bytes, firma: str) -> Optional[ResultadoWebhook]:
        datos = json.loads(cuerpo.decode() or "{}")
        ref = datos.get("referencia")
        return ResultadoWebhook(referencia=ref, aprobado=bool(datos.get("aprobado", True))) if ref else None
