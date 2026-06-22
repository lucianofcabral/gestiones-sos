"""EliminarFactura — delete an Invoice by invoice_id with document integrity check."""

from uuid import UUID

from src.domain.ports.repositories import BillingRepoPort, DocumentRepoPort


class EliminarFactura:
    """Delete an Invoice by invoice_id.

    Raises ValueError if any DocumentEntity references the invoice_id.
    Returns True on success, False if the invoice does not exist.
    """

    def __init__(
        self,
        billing_repo: BillingRepoPort,
        document_repo: DocumentRepoPort,
    ) -> None:
        self._billing_repo = billing_repo
        self._document_repo = document_repo

    def execute(self, invoice_id: UUID) -> bool:
        invoice = self._billing_repo.get_by_id(invoice_id)
        if invoice is None:
            return False

        if self._document_repo.get_by_billing_id(invoice_id) is not None:
            raise ValueError(
                "No se puede eliminar una factura con documentos asociados"
            )

        self._billing_repo.delete(invoice_id)
        return True
