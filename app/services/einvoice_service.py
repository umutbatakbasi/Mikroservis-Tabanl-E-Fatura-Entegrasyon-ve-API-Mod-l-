from abc import ABC, abstractmethod
from typing import Dict, Any
import uuid
from app.models.invoice_header import InvoiceHeader, InvoiceStatus


class BaseEInvoiceService(ABC):
    """Abstract base class for E-Invoice integration (GİB, Özel Entegratörler veya Mock)."""

    @abstractmethod
    def send_invoice(self, invoice: InvoiceHeader) -> Dict[str, Any]:
        """Send an invoice to the e-invoice portal/integrator."""
        pass

    @abstractmethod
    def get_status(self, invoice_uuid: str) -> Dict[str, Any]:
        """Query the status of a sent invoice by its UUID."""
        pass


class MockEInvoiceService(BaseEInvoiceService):
    """Mock implementation of the E-Invoice service for development and testing."""

    def send_invoice(self, invoice: InvoiceHeader) -> Dict[str, Any]:
        """Simulate transmitting the invoice to GİB/Integrator and getting approval."""
        generated_uuid = str(uuid.uuid4())
        return {
            "success": True,
            "uuid": generated_uuid,
            "status": InvoiceStatus.ACCEPTED.value,
            "message": "Fatura GİB sistemine başarıyla iletildi ve 'ACCEPTED' olarak onaylandı.",
        }

    def get_status(self, invoice_uuid: str) -> Dict[str, Any]:
        """Simulate status inquiry."""
        return {
            "uuid": invoice_uuid,
            "status": InvoiceStatus.ACCEPTED.value,
            "description": "Fatura alıcıya ulaştırıldı.",
        }


class GibEInvoiceService(BaseEInvoiceService):
    """Placeholder implementation for future real GİB (Gelir İdaresi Başkanlığı) E-Fatura API integration."""

    def __init__(self, api_key: str = "", endpoint_url: str = ""):
        self.api_key = api_key
        self.endpoint_url = endpoint_url

    def send_invoice(self, invoice: InvoiceHeader) -> Dict[str, Any]:
        # Gerçek entegratör (UBL-TR 1.2 XML formatlama, şematron kontrolü ve SOAP/REST API çağrısı)
        raise NotImplementedError("GİB canlı entegrasyon servisi henüz konfigüre edilmedi.")

    def get_status(self, invoice_uuid: str) -> Dict[str, Any]:
        raise NotImplementedError("GİB canlı durum sorgulama servisi henüz konfigüre edilmedi.")


def get_einvoice_service() -> BaseEInvoiceService:
    """Dependency provider / factory for E-Invoice Service."""
    return MockEInvoiceService()
