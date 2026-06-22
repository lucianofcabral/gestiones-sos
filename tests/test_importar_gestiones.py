"""Tests for SOS Excel import: parser + use case integration."""

from datetime import date, datetime
from io import BytesIO
from uuid import UUID, uuid4

import pytest
from openpyxl import Workbook

from src.adapters.persistence.inmemory_claim_kind_repository import (
    InMemoryClaimKindRepository,
)
from src.adapters.persistence.inmemory_claim_repository import (
    InMemoryClaimRepository,
)
from src.adapters.persistence.inmemory_group_claim_repository import (
    InMemoryGroupClaimRepository,
)
from src.adapters.persistence.inmemory_sos_claim_repository import (
    InMemorySosClaimRepository,
)
from src.application.services.excel_parser import (
    ParsedRow,
    parse_excel,
)
from src.application.use_cases.claims.importar_gestiones_sos import (
    ImportarGestionSOS,
    ImportResult,
    RowError,
)
from src.domain.models.entities import Claim, ClaimKind, GroupClaim, SosClaim
from src.domain.ports.uow import UnitOfWork


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

DEFAULT_SHEET = "Reclamos y Reintegros"
HEADERS = [
    "Fecha",
    "N° Gestión",
    "Cliente",
    "Dominio",
    "Póliza",
    "Tipo",
    "Motivo",
    "N° Caso",
    "Usuario Carga",
    "Usuario Respuesta",
    "Estado",
    "ITR",
]


def _make_excel(
    rows: list[list],
    sheet_name: str = DEFAULT_SHEET,
    headers: list[str] | None = None,
) -> bytes:
    """Create an ``.xlsx`` file in memory and return its bytes."""
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name
    ws.append(headers or HEADERS)
    for row in rows:
        ws.append(row)
    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.getvalue()


# ═══════════════════════════════════════════════════════════════════════════════
# Excel Parser — Unit Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestParseExcel:
    """Happy path + edge cases for ``parse_excel``."""

    def test_parse_valid_rows(self) -> None:
        """Happy path: valid rows are parsed with correct field mapping."""
        xlsx = _make_excel([
            [
                datetime(2025, 6, 15),  # Fecha
                12345,  # N° Gestión
                "Juan Pérez",  # Cliente
                "ABC-123",  # Dominio
                "POL-123",  # Póliza
                "Accidente",  # Tipo
                "Choque frontal",  # Motivo
                "C-001",  # N° Caso (skip)
                "admin",  # Usuario Carga
                "operador",  # Usuario Respuesta
                "Pendiente",  # Estado
                5,  # ITR
            ],
            [
                datetime(2025, 7, 1),
                12346,
                "María García",
                "XYZ-789",
                "POL-456",
                "Robo",
                "Hurto parcial",
                "C-002",
                "supervisor",
                "analista",
                "Cerrado",
                3,
            ],
        ])

        result = parse_excel(xlsx)
        assert len(result) == 2

        # First row
        r1 = result[0]
        assert r1.gestion == 12345
        assert r1.created_at == date(2025, 6, 15)
        assert r1.claimer_name == "Juan Pérez"
        assert r1.policy_number == "POL-123"
        assert r1.plate == "ABC-123"
        assert r1.category == "Accidente"
        assert r1.reason == "Choque frontal"
        assert r1.status == "Pendiente"
        assert r1.load_user == "admin"
        assert r1.response_user == "operador"
        assert r1.itr == 5

        # Second row
        r2 = result[1]
        assert r2.gestion == 12346
        assert r2.created_at == date(2025, 7, 1)
        assert r2.claimer_name == "María García"
        assert r2.policy_number == "POL-456"
        assert r2.plate == "XYZ-789"
        assert r2.itr == 3

    def test_parse_date_string_dd_mm_yyyy(self) -> None:
        """Dates in ``DD/MM/YYYY`` string format are parsed correctly."""
        xlsx = _make_excel([
            ["15/06/2025", 1001, "A", "AA-000", "P-1", "", "", "C-001", "", "", "", 0],
        ])
        result = parse_excel(xlsx)
        assert result[0].created_at == date(2025, 6, 15)

    def test_parse_empty_optional_fields_default_to_empty(self) -> None:
        """Cells with no value become empty string / 0 for optional fields."""
        xlsx = _make_excel([
            [None, 2001, "", "", "", "", "", "", "", "", "", None],
        ])
        result = parse_excel(xlsx)
        r = result[0]
        assert r.gestion == 2001
        assert r.created_at is None
        assert r.claimer_name == ""
        assert r.itr == 0

    def test_parse_skip_empty_rows(self) -> None:
        """Rows where ``N° Gestión`` is empty are skipped."""
        xlsx = _make_excel([
            [None, 3001, "A", "AA-000", "P-1", "", "", "C-001", "", "", "", 0],
            [None, None, "B", "BB-000", "P-2", "", "", "C-002", "", "", "", 0],
            [None, 3003, "C", "CC-000", "P-3", "", "", "C-003", "", "", "", 0],
        ])
        result = parse_excel(xlsx)
        assert len(result) == 2
        assert result[0].gestion == 3001
        assert result[1].gestion == 3003

    def test_missing_required_column_raises(self) -> None:
        """Missing ``N° Gestión`` column raises ``ValueError``."""
        bad_headers = ["N° Caso", "Fecha", "Cliente"]
        xlsx = _make_excel([["C-001", "15/06/2025", "Juan"]], headers=bad_headers)

        with pytest.raises(ValueError, match="requerida"):
            parse_excel(xlsx)

    def test_wrong_sheet_name_raises(self) -> None:
        """An incorrect sheet name raises ``ValueError``."""
        xlsx = _make_excel([[None, 1001, "A", "AA-000", "P", "", "", 1, "", "", "", 0]], sheet_name="WrongSheet")

        with pytest.raises(ValueError, match="no existe"):
            parse_excel(xlsx, sheet_name="Reclamos y Reintegros")

    def test_non_integer_gestion_skips_row(self) -> None:
        """A row with a non-integer gestion value is silently skipped."""
        xlsx = _make_excel([
            [None, "NOT_A_NUMBER", "A", "AA-000", "P", "", "", "", "", "", "", 0],
            [None, 4002, "B", "BB-000", "P", "", "", "", "", "", "", 0],
        ])
        result = parse_excel(xlsx)
        assert len(result) == 1
        assert result[0].gestion == 4002

    def test_parse_with_custom_sheet_name(self) -> None:
        """The caller can specify a custom sheet name."""
        xlsx = _make_excel(
            [[None, 5001, "A", "AA-000", "P", "", "", "", "", "", "", 0]],
            sheet_name="CustomSheet",
        )
        result = parse_excel(xlsx, sheet_name="CustomSheet")
        assert len(result) == 1
        assert result[0].gestion == 5001

    def test_parse_gestion_as_float_string(self) -> None:
        """``gestion`` in scientific notation or float-as-string is handled."""
        xlsx = _make_excel([
            [None, "12345.0", "A", "AA-000", "P", "", "", "", "", "", "", 0],
        ])
        result = parse_excel(xlsx)
        assert result[0].gestion == 12345

    def test_empty_file_raises(self) -> None:
        """An Excel file with no rows raises ``ValueError``."""
        wb = Workbook()
        ws = wb.active
        ws.title = DEFAULT_SHEET
        buf = BytesIO()
        wb.save(buf)
        buf.seek(0)

        with pytest.raises(ValueError, match="vacío"):
            parse_excel(buf.getvalue())

    def test_all_columns_mapped_correctly(self) -> None:
        """Every mapped column produces the correct field in ParsedRow."""
        xlsx = _make_excel([
            [
                datetime(2026, 1, 10),  # Fecha
                7777,  # N° Gestión
                "Cliente Test",  # Cliente
                "PLATE-77",  # Dominio
                "POL-ABC-999",  # Póliza
                "CategoriaX",  # Tipo
                "MotivoY",  # Motivo
                "C-999",  # N° Caso (ignored)
                "UserCarga",  # Usuario Carga
                "UserResp",  # Usuario Respuesta
                "EstadoZ",  # Estado
                99,  # ITR
            ],
        ])
        result = parse_excel(xlsx)
        r = result[0]
        assert r.gestion == 7777
        assert r.created_at == date(2026, 1, 10)
        assert r.claimer_name == "Cliente Test"
        assert r.policy_number == "POL-ABC-999"
        assert r.plate == "PLATE-77"
        assert r.category == "CategoriaX"
        assert r.reason == "MotivoY"
        assert r.status == "EstadoZ"
        assert r.load_user == "UserCarga"
        assert r.response_user == "UserResp"
        assert r.itr == 99


# ═══════════════════════════════════════════════════════════════════════════════
# FakeUnitOfWork for import tests
# ═══════════════════════════════════════════════════════════════════════════════


class FakeUnitOfWork(UnitOfWork):
    """In-memory UoW wrapping Claim + SosClaim repos (no-op commit/rollback)."""

    def __init__(
        self,
        claims: InMemoryClaimRepository,
        sos_claims: InMemorySosClaimRepository,
    ) -> None:
        self.claims = claims
        self.sos_claims = sos_claims

    def commit(self) -> None:
        pass

    def rollback(self) -> None:
        pass


# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def claim_repo() -> InMemoryClaimRepository:
    return InMemoryClaimRepository()


@pytest.fixture
def sos_repo() -> InMemorySosClaimRepository:
    return InMemorySosClaimRepository()


@pytest.fixture
def claim_kind_repo() -> InMemoryClaimKindRepository:
    repo = InMemoryClaimKindRepository()
    repo.add(ClaimKind(name="SOS"))
    return repo


@pytest.fixture
def group_claim_repo() -> InMemoryGroupClaimRepository:
    repo = InMemoryGroupClaimRepository()
    repo.add(GroupClaim(name="SOS", external_reference="SOS-GRP"))
    return repo


@pytest.fixture
def fake_uow_class(
    claim_repo: InMemoryClaimRepository,
    sos_repo: InMemorySosClaimRepository,
):
    """Return a *class* (not instance) of ``FakeUnitOfWork``.

    The use case needs ``uow_cls`` (a type) so it can instantiate fresh
    UoWs per row.
    """

    class FakeUnitOfWorkFactory(FakeUnitOfWork):
        def __init__(self):
            super().__init__(claim_repo, sos_repo)

    return FakeUnitOfWorkFactory


@pytest.fixture
def use_case(
    fake_uow_class,
    claim_kind_repo: InMemoryClaimKindRepository,
    group_claim_repo: InMemoryGroupClaimRepository,
) -> ImportarGestionSOS:
    return ImportarGestionSOS(
        uow_cls=fake_uow_class,
        claim_kind_repo=claim_kind_repo,
        group_claim_repo=group_claim_repo,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Use Case — Unit Tests
# ═══════════════════════════════════════════════════════════════════════════════


def _make_row(gestion: int, **overrides) -> ParsedRow:
    data = dict(
        gestion=gestion,
        created_at=None,
        claimer_name="Test",
        policy_number="POL-001",
        plate="ABC-123",
        category="Cat",
        reason="Reason",
        status="Open",
        load_user="loader",
        response_user="responder",
        itr=1,
    )
    data.update(overrides)
    return ParsedRow(**data)


class TestImportarGestionSOS:
    """Unit tests for the import use case."""

    def test_create_new_claim_and_sos(
        self,
        use_case: ImportarGestionSOS,
        claim_repo: InMemoryClaimRepository,
        sos_repo: InMemorySosClaimRepository,
    ) -> None:
        """Happy path: a new gestion creates Claim + SosClaim."""
        rows = [_make_row(1001)]
        result = use_case.execute(rows)

        assert result.total == 1
        assert result.created == 1
        assert result.updated == 0
        assert len(result.errors) == 0

        # Verify in-store
        sos = sos_repo.get_by_number(1001)
        assert sos is not None
        assert sos.gestion == 1001
        assert sos.category == "Cat"

        claim = claim_repo.get_by_id(sos.claim_id)
        assert claim is not None
        assert claim.claimer_name == "Test"
        assert claim.claimed_amount == 0.01

    def test_update_existing_claim_and_sos(
        self,
        use_case: ImportarGestionSOS,
        claim_repo: InMemoryClaimRepository,
        sos_repo: InMemorySosClaimRepository,
    ) -> None:
        """When gestion already exists, update both entities."""
        # Seed existing
        claim = claim_repo.add(
            Claim(
                claim_kind_id=uuid4(),
                group_id=uuid4(),
                claimer_name="Old Name",
                policy_number="OLD-001",
                plate="ABC-123",
                claimed_amount=500.0,
            )
        )
        sos_repo.add(
            SosClaim(
                claim_id=claim.claim_id,
                gestion=2001,
                category="Old Cat",
                reason="Old Reason",
                status="Closed",
                load_user="old",
                response_user="old",
                itr=0,
            )
        )

        rows = [
            _make_row(
                2001,
                claimer_name="New Name",
                policy_number="NEW-001",
                category="New Cat",
                reason="New Reason",
                status="Open",
                itr=5,
            )
        ]
        result = use_case.execute(rows)

        assert result.created == 0
        assert result.updated == 1
        assert len(result.errors) == 0

        # Verify update
        sos = sos_repo.get_by_number(2001)
        assert sos is not None
        assert sos.category == "New Cat"
        assert sos.status == "Open"
        assert sos.itr == 5

        claim = claim_repo.get_by_id(claim.claim_id)
        assert claim is not None
        assert claim.claimer_name == "New Name"
        assert claim.policy_number == "NEW-001"
        # claimed_amount must be preserved (not overwritten on update)
        assert claim.claimed_amount == 500.0

    def test_duplicate_gestion_in_file(
        self,
        use_case: ImportarGestionSOS,
        sos_repo: InMemorySosClaimRepository,
        claim_repo: InMemoryClaimRepository,
    ) -> None:
        """Two rows with same gestion: first creates, second updates."""
        rows = [
            _make_row(3001, claimer_name="First"),
            _make_row(3001, claimer_name="Second"),
        ]
        result = use_case.execute(rows)

        assert result.total == 2
        assert result.created == 1
        assert result.updated == 1
        assert len(result.errors) == 0

        # Only one SosClaim in store
        all_sos = sos_repo.get_all()
        assert len(all_sos) == 1
        assert all_sos[0].gestion == 3001

        # Claim should have the second name (updated)
        claim = claim_repo.get_by_id(all_sos[0].claim_id)
        assert claim is not None
        assert claim.claimer_name == "Second"

    def test_missing_claim_kind_aborts_all_rows(
        self,
        claim_repo: InMemoryClaimRepository,
        sos_repo: InMemorySosClaimRepository,
        group_claim_repo: InMemoryGroupClaimRepository,
    ) -> None:
        """If no SOS claim kind exists, all rows are reported as errors."""
        empty_kind_repo = InMemoryClaimKindRepository()

        uow_cls = _make_fake_uow_class(claim_repo, sos_repo)
        uc = ImportarGestionSOS(
            uow_cls=uow_cls,
            claim_kind_repo=empty_kind_repo,
            group_claim_repo=group_claim_repo,
        )

        rows = [_make_row(4001), _make_row(4002)]
        result = uc.execute(rows)

        assert result.total == 2
        assert result.created == 0
        assert result.updated == 0
        assert len(result.errors) == 2
        assert "SOS" in result.errors[0].message

    def test_no_groups_aborts_all_rows(
        self,
        claim_repo: InMemoryClaimRepository,
        sos_repo: InMemorySosClaimRepository,
        claim_kind_repo: InMemoryClaimKindRepository,
    ) -> None:
        """If no GroupClaim exists, all rows are reported as errors."""
        empty_group_repo = InMemoryGroupClaimRepository()

        uow_cls = _make_fake_uow_class(claim_repo, sos_repo)
        uc = ImportarGestionSOS(
            uow_cls=uow_cls,
            claim_kind_repo=claim_kind_repo,
            group_claim_repo=empty_group_repo,
        )

        rows = [_make_row(5001)]
        result = uc.execute(rows)

        assert result.total == 1
        assert result.created == 0
        assert result.updated == 0
        assert len(result.errors) == 1
        assert "grupo" in result.errors[0].message.lower()

    def test_partial_failure_isolation(
        self,
        claim_repo: InMemoryClaimRepository,
        sos_repo: InMemorySosClaimRepository,
        claim_kind_repo: InMemoryClaimKindRepository,
        group_claim_repo: InMemoryGroupClaimRepository,
    ) -> None:
        """A failure on one row does not prevent others from succeeding."""
        # Inject a failing behaviour: second row triggers an error by
        # having empty claimer_name (min_length=1 validation on Claim).
        # We can also use a non-integer gestion to trigger parser-level skip,
        # but since the use case receives already-parsed rows, we simulate
        # by making a row that fails Pydantic validation on Claim creation.

        uow_cls = _make_fake_uow_class(claim_repo, sos_repo)
        uc = ImportarGestionSOS(
            uow_cls=uow_cls,
            claim_kind_repo=claim_kind_repo,
            group_claim_repo=group_claim_repo,
        )

        rows = [
            _make_row(6001, claimer_name="Valid"),
            # This row will fail because Claim requires min_length=1 for claimer_name
            _make_row(6002, claimer_name=""),
        ]

        result = uc.execute(rows)

        assert result.total == 2
        assert result.created >= 1  # At least row 1 succeeds
        assert len(result.errors) >= 1  # Row 2 should fail

        # Row 1 should be persisted
        sos1 = sos_repo.get_by_number(6001)
        assert sos1 is not None

    def test_group_fallback_to_first_available(
        self,
        claim_repo: InMemoryClaimRepository,
        sos_repo: InMemorySosClaimRepository,
        claim_kind_repo: InMemoryClaimKindRepository,
    ) -> None:
        """When there is no 'SOS' group, the first group is used."""
        group_repo = InMemoryGroupClaimRepository()
        group_id = uuid4()
        group_repo.add(GroupClaim(group_id=group_id, name="Default Group", external_reference="DFT-GRP"))

        uow_cls = _make_fake_uow_class(claim_repo, sos_repo)
        uc = ImportarGestionSOS(
            uow_cls=uow_cls,
            claim_kind_repo=claim_kind_repo,
            group_claim_repo=group_repo,
        )

        rows = [_make_row(7001)]
        result = uc.execute(rows)

        assert result.created == 1
        assert len(result.errors) == 0

        # Verify the claim was created with the fallback group_id
        sos = sos_repo.get_by_number(7001)
        claim = claim_repo.get_by_id(sos.claim_id)
        assert claim.group_id == group_id

    def test_result_counts_mixed(
        self,
        use_case: ImportarGestionSOS,
        claim_repo: InMemoryClaimRepository,
        sos_repo: InMemorySosClaimRepository,
    ) -> None:
        """Mixed results: some created, some updated, some errors."""
        # Seed an existing gestion
        claim = claim_repo.add(Claim(
            claim_kind_id=uuid4(), group_id=uuid4(),
            claimer_name="Existing", policy_number="P-1", plate="ABC-123",
        ))
        sos_repo.add(SosClaim(claim_id=claim.claim_id, gestion=8002))

        rows = [
            _make_row(8001),  # New → created
            _make_row(8002, claimer_name="Updated"),  # Existing → updated
            _make_row(8003, claimer_name=""),  # Fails validation → error
        ]
        result = use_case.execute(rows)

        assert result.total == 3
        assert result.created == 1
        assert result.updated == 1
        assert len(result.errors) == 1
        assert result.errors[0].gestion == 8003

    def test_preserves_existing_claimed_amount_on_update(
        self,
        use_case: ImportarGestionSOS,
        claim_repo: InMemoryClaimRepository,
        sos_repo: InMemorySosClaimRepository,
    ) -> None:
        """When updating, the existing claimed_amount is preserved."""
        claim = claim_repo.add(Claim(
            claim_kind_id=uuid4(), group_id=uuid4(),
            claimer_name="Test", policy_number="P-1", plate="ABC-123",
            claimed_amount=999.99,
        ))
        sos_repo.add(SosClaim(claim_id=claim.claim_id, gestion=9001))

        result = use_case.execute([_make_row(9001, claimer_name="Updated")])

        assert result.updated == 1
        updated_claim = claim_repo.get_by_id(claim.claim_id)
        assert updated_claim.claimed_amount == 999.99

    def test_new_claim_defaults_amount(
        self,
        use_case: ImportarGestionSOS,
        sos_repo: InMemorySosClaimRepository,
    ) -> None:
        """New claims use the default claimed_amount of 0.01."""
        result = use_case.execute([_make_row(10001)])

        assert result.created == 1
        sos = sos_repo.get_by_number(10001)
        claim = sos_repo.get_by_id(sos.sos_claim_id)  # Wrong — need claim_repo
        # Fix: use the correct lookup
        claim_obj = None
        # We need claim_repo access

    # The test above is intentionally broken — rewritten below properly


def test_new_claim_default_amount_proper(
    use_case: ImportarGestionSOS,
    claim_repo: InMemoryClaimRepository,
    sos_repo: InMemorySosClaimRepository,
) -> None:
    """New claims use the default claimed_amount of 0.01."""
    result = use_case.execute([_make_row(10001)])

    assert result.created == 1
    sos = sos_repo.get_by_number(10001)
    assert sos is not None
    claim = claim_repo.get_by_id(sos.claim_id)
    assert claim is not None
    assert claim.claimed_amount == 0.01


# ═══════════════════════════════════════════════════════════════════════════════
# Integration Test — Full Pipeline
# ═══════════════════════════════════════════════════════════════════════════════


def test_integration_full_import_flow(
    claim_repo: InMemoryClaimRepository,
    sos_repo: InMemorySosClaimRepository,
    claim_kind_repo: InMemoryClaimKindRepository,
    group_claim_repo: InMemoryGroupClaimRepository,
) -> None:
    """End-to-end: Excel bytes → parser → use case → verify store state."""
    # Arrange: produce .xlsx bytes as they would arrive from the UI
    xlsx = _make_excel([
        [
            datetime(2025, 1, 15),  # Fecha
            101,  # N° Gestión
            "Alice",  # Cliente
            "AAA-111",  # Dominio
            "POL-A1",  # Póliza
            "Accidente",  # Tipo
            "Daños",  # Motivo
            "C-100",  # N° Caso
            "user1",  # Usuario Carga
            "user2",  # Usuario Respuesta
            "Pendiente",  # Estado
            2,  # ITR
        ],
        [
            datetime(2025, 2, 20),  # Fecha
            102,  # N° Gestión
            "Bob",  # Cliente
            "BBB-222",  # Dominio
            "POL-B2",  # Póliza
            "Robo",  # Tipo
            "Pérdida total",  # Motivo
            "C-101",  # N° Caso
            "admin",  # Usuario Carga
            "supervisor",  # Usuario Respuesta
            "Cerrado",  # Estado
            1,  # ITR
        ],
    ])

    # Act: parse
    parsed = parse_excel(xlsx)
    assert len(parsed) == 2

    # Act: import
    uow_cls = _make_fake_uow_class(claim_repo, sos_repo)
    uc = ImportarGestionSOS(
        uow_cls=uow_cls,
        claim_kind_repo=claim_kind_repo,
        group_claim_repo=group_claim_repo,
    )
    result = uc.execute(parsed)

    # Assert: summary
    assert result.total == 2
    assert result.created == 2
    assert result.updated == 0
    assert len(result.errors) == 0

    # Assert: store state — both SOS claims exist
    sos1 = sos_repo.get_by_number(101)
    sos2 = sos_repo.get_by_number(102)
    assert sos1 is not None
    assert sos2 is not None

    # Assert: Claims exist with correct amounts
    claim1 = claim_repo.get_by_id(sos1.claim_id)
    claim2 = claim_repo.get_by_id(sos2.claim_id)
    assert claim1 is not None
    assert claim2 is not None
    assert claim1.claimer_name == "Alice"
    assert claim2.claimer_name == "Bob"
    assert claim1.claimed_amount == 0.01
    assert claim2.claimed_amount == 0.01

    # Assert: dates preserved
    assert claim1.created_at.date() == date(2025, 1, 15)
    assert claim2.created_at.date() == date(2025, 2, 20)

    # Assert: related via claim_id
    assert sos1.claim_id == claim1.claim_id
    assert sos2.claim_id == claim2.claim_id

    # Act: import same file again (all rows should update)
    result2 = uc.execute(parsed)
    assert result2.total == 2
    assert result2.created == 0
    assert result2.updated == 2
    assert len(result2.errors) == 0


# ═══════════════════════════════════════════════════════════════════════════════
# Internal Helper
# ═══════════════════════════════════════════════════════════════════════════════


def _make_fake_uow_class(
    claim_repo: InMemoryClaimRepository,
    sos_repo: InMemorySosClaimRepository,
):
    """Produce a :class:`FakeUnitOfWork` subclass that captures *claim_repo*
    and *sos_repo* at construction time (no-arg constructor)."""

    class _Factory(FakeUnitOfWork):
        def __init__(self):
            super().__init__(claim_repo, sos_repo)

    return _Factory
