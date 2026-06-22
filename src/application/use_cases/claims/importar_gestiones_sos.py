"""Use case to import multiple SOS gestiones from parsed Excel rows.

Each row is processed in its own Unit of Work transaction for error isolation.
"""

from dataclasses import dataclass, field
from datetime import datetime

from src.application.services.excel_parser import ParsedRow
from src.domain.models.entities import Claim, SosClaim
from src.domain.ports.repositories import ClaimKindRepoPort, GroupClaimRepoPort
from src.domain.ports.uow import UnitOfWork


# ── DTOs ──────────────────────────────────────────────────────────────────────


@dataclass
class RowError:
    """Information about a single row that failed during import."""

    row_index: int
    gestion: int | None = None
    message: str = ""


@dataclass
class ImportResult:
    """Aggregated result of the entire import operation."""

    total: int = 0
    created: int = 0
    updated: int = 0
    errors: list[RowError] = field(default_factory=list)


# ── Use case ──────────────────────────────────────────────────────────────────


class ImportarGestionSOS:
    """Import SOS gestiones from parsed Excel rows.

    Each row is processed in its own UoW transaction so that a failure on
    one row does not affect the others.
    """

    SOS_KIND_NAME = "SOS"
    DEFAULT_CLAIMED_AMOUNT = 0.01

    def __init__(
        self,
        uow_cls: type[UnitOfWork],
        claim_kind_repo: ClaimKindRepoPort,
        group_claim_repo: GroupClaimRepoPort,
    ) -> None:
        self._uow_cls = uow_cls
        self._claim_kind_repo = claim_kind_repo
        self._group_claim_repo = group_claim_repo

    # ── Public API ──────────────────────────────────────────────────────────

    def execute(self, rows: list[ParsedRow]) -> ImportResult:
        """Run the import for the given parsed rows.

        Steps:
        1. Resolve ``claim_kind_id`` for "SOS".
        2. Resolve a default ``group_id``.
        3. For each row, open a fresh UoW and either create or update.

        Returns:
            An :class:`ImportResult` with summary counts and per-row errors.
        """
        result = ImportResult(total=len(rows))

        # 1. Pre-resolve claim_kind_id
        claim_kind = self._claim_kind_repo.get_by_name(self.SOS_KIND_NAME)
        if claim_kind is None:
            for i in range(len(rows)):
                result.errors.append(
                    RowError(
                        row_index=i,
                        gestion=rows[i].gestion if i < len(rows) else None,
                        message=(
                            "No se encontró un tipo de reclamo "
                            f"'{self.SOS_KIND_NAME}' en el sistema."
                        ),
                    )
                )
            return result

        # 2. Pre-resolve group_id
        group_id = self._resolve_group_id()
        if group_id is None:
            for i in range(len(rows)):
                result.errors.append(
                    RowError(
                        row_index=i,
                        gestion=rows[i].gestion if i < len(rows) else None,
                        message="No se encontró ningún grupo configurado en el sistema.",
                    )
                )
            return result

        claim_kind_id = claim_kind.claim_kind_id

        # 3. Process each row in its own transaction
        for i, row in enumerate(rows):
            try:
                with self._uow_cls() as uow:
                    existing_sos = uow.sos_claims.get_by_number(row.gestion)

                    if existing_sos is not None:
                        self._update_row(uow, existing_sos, row)
                        result.updated += 1
                    else:
                        self._create_row(uow, claim_kind_id, group_id, row)
                        result.created += 1
            except Exception as exc:
                result.errors.append(
                    RowError(
                        row_index=i,
                        gestion=row.gestion,
                        message=str(exc),
                    )
                )

        return result

    # ── Internal helpers ────────────────────────────────────────────────────

    def _resolve_group_id(self):
        """Resolve a default group ID — try "SOS" by name, then first available."""
        group = self._group_claim_repo.get_by_group_name(self.SOS_KIND_NAME)
        if group is not None:
            return group.group_id

        all_groups = self._group_claim_repo.get_all()
        if all_groups:
            return all_groups[0].group_id

        return None

    def _update_row(self, uow: UnitOfWork, existing_sos: SosClaim, row: ParsedRow) -> None:
        """Update an existing SosClaim and its linked Claim."""
        claim = uow.claims.get_by_id(existing_sos.claim_id)
        if claim is None:
            raise ValueError(
                f"Claim vinculado no encontrado para la gestión {row.gestion}"
            )

        # Update Claim fields keeping existing values where the import row is empty
        updated_claim = claim.model_copy(
            update={
                "claimer_name": row.claimer_name if row.claimer_name else claim.claimer_name,
                "policy_number": row.policy_number if row.policy_number else claim.policy_number,
                "plate": row.plate if row.plate else claim.plate,
            }
        )
        uow.claims.update(claim.claim_id, updated_claim)

        # Update SosClaim fields
        updated_sos = existing_sos.model_copy(
            update={
                "category": row.category,
                "reason": row.reason,
                "load_user": row.load_user,
                "response_user": row.response_user,
                "status": row.status,
                "itr": row.itr,
            }
        )
        uow.sos_claims.update(existing_sos.sos_claim_id, updated_sos)

    def _create_row(
        self,
        uow: UnitOfWork,
        claim_kind_id,
        group_id,
        row: ParsedRow,
    ) -> None:
        """Create a new Claim + SosClaim from a parsed row."""
        now = datetime.now()
        if row.created_at is not None:
            created_at = datetime.combine(row.created_at, now.time())
        else:
            created_at = now

        claim = uow.claims.add(
            Claim(
                claim_kind_id=claim_kind_id,
                group_id=group_id,
                claimer_name=row.claimer_name,
                policy_number=row.policy_number,
                plate=row.plate,
                claimed_amount=self.DEFAULT_CLAIMED_AMOUNT,
                created_at=created_at,
            )
        )

        uow.sos_claims.add(
            SosClaim(
                claim_id=claim.claim_id,
                gestion=row.gestion,
                category=row.category,
                reason=row.reason,
                load_user=row.load_user,
                response_user=row.response_user,
                status=row.status,
                itr=row.itr,
            )
        )
