"""Unit tests for GroupClaim repos and use cases using in-memory implementations."""

from uuid import UUID, uuid4

import pytest

from src.adapters.persistence.inmemory_claim_repository import (
    InMemoryClaimRepository,
)
from src.adapters.persistence.inmemory_group_claim_repository import (
    InMemoryGroupClaimRepository,
)
from src.application.use_cases.claims.actualizar_grupo import ActualizarGrupo
from src.application.use_cases.claims.eliminar_grupo import EliminarGrupo
from src.application.use_cases.claims.obtener_grupos import ObtenerGrupos
from src.application.use_cases.claims.registrar_grupo import RegistrarGrupo
from src.domain.models.entities import Claim, GroupClaim


# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def claim_repo() -> InMemoryClaimRepository:
    return InMemoryClaimRepository()


@pytest.fixture
def group_repo() -> InMemoryGroupClaimRepository:
    return InMemoryGroupClaimRepository()


@pytest.fixture
def group_repo_with_claims(
    claim_repo: InMemoryClaimRepository,
) -> InMemoryGroupClaimRepository:
    return InMemoryGroupClaimRepository(claim_store=claim_repo._store)


# ═══════════════════════════════════════════════════════════════════════════════
# Seed helpers
# ═══════════════════════════════════════════════════════════════════════════════


def _seed_group(
    repo: InMemoryGroupClaimRepository,
    group_id: UUID | None = None,
    name: str = "Test Group",
) -> GroupClaim:
    gid = group_id or uuid4()
    group = GroupClaim(group_id=gid, name=name, external_reference=f"GRP-{name}")
    repo.add(group)
    return group


def _seed_claim(
    repo: InMemoryClaimRepository,
    claim_id: UUID | None = None,
    group_id: UUID | None = None,
) -> Claim:
    cid = claim_id or uuid4()
    gid = group_id or uuid4()
    claim = Claim(
        claim_id=cid,
        claim_kind_id=uuid4(),
        group_id=gid,
        claimer_name="Test Claimer",
        policy_number="POL001",
        plate="ABC123",
    )
    repo.add(claim)
    return claim


# ═══════════════════════════════════════════════════════════════════════════════
# InMemoryGroupClaimRepository Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestGroupClaimRepo:
    """Tests for InMemoryGroupClaimRepository — BaseRepo + GroupClaimRepoPort."""

    # ── BaseRepo: get_by_id ────────────────────────────────────────────────

    def test_get_by_id_returns_group_when_found(
        self, group_repo: InMemoryGroupClaimRepository
    ) -> None:
        group = _seed_group(group_repo)

        result = group_repo.get_by_id(group.group_id)

        assert result is not None
        assert result.group_id == group.group_id
        assert result.name == group.name

    def test_get_by_id_returns_none_when_not_found(
        self, group_repo: InMemoryGroupClaimRepository
    ) -> None:
        result = group_repo.get_by_id(uuid4())
        assert result is None

    # ── BaseRepo: add ──────────────────────────────────────────────────────

    def test_add_stores_group(self, group_repo: InMemoryGroupClaimRepository) -> None:
        group = GroupClaim(name="New Group", group_id=uuid4(), external_reference="GRP-New-Group")

        result = group_repo.add(group)

        assert result == group
        assert group_repo.get_by_id(group.group_id) == group

    # ── BaseRepo: get_all ──────────────────────────────────────────────────

    def test_get_all_returns_all_groups(
        self, group_repo: InMemoryGroupClaimRepository
    ) -> None:
        g1 = _seed_group(group_repo, name="Grupo A")
        g2 = _seed_group(group_repo, name="Grupo B")

        result = group_repo.get_all()

        assert len(result) == 2
        assert g1 in result
        assert g2 in result

    def test_get_all_returns_empty_when_no_groups(
        self, group_repo: InMemoryGroupClaimRepository
    ) -> None:
        result = group_repo.get_all()
        assert result == []

    # ── BaseRepo: exists ───────────────────────────────────────────────────

    def test_exists_returns_true_when_match(
        self, group_repo: InMemoryGroupClaimRepository
    ) -> None:
        _seed_group(group_repo, name="Grupo Unico")

        assert group_repo.exists({"name": "Grupo Unico"}) is True

    def test_exists_returns_false_when_no_match(
        self, group_repo: InMemoryGroupClaimRepository
    ) -> None:
        _seed_group(group_repo, name="Grupo Unico")

        assert group_repo.exists({"name": "Otro Grupo"}) is False

    # ── BaseRepo: update ───────────────────────────────────────────────────

    def test_update_returns_true_and_modifies(
        self, group_repo: InMemoryGroupClaimRepository
    ) -> None:
        group = _seed_group(group_repo, name="Original")
        updated = GroupClaim(
            group_id=group.group_id, name="Modificado", external_reference=group.external_reference, created_at=group.created_at
        )

        result = group_repo.update(group.group_id, updated)

        assert result is True
        stored = group_repo.get_by_id(group.group_id)
        assert stored is not None
        assert stored.name == "Modificado"

    def test_update_returns_false_when_not_found(
        self, group_repo: InMemoryGroupClaimRepository
    ) -> None:
        g = GroupClaim(name="Ghost", external_reference="GRP-Ghost")
        result = group_repo.update(g.group_id, g)
        assert result is False

    # ── BaseRepo: delete ───────────────────────────────────────────────────

    def test_delete_removes_group(
        self, group_repo: InMemoryGroupClaimRepository
    ) -> None:
        group = _seed_group(group_repo)

        group_repo.delete(group.group_id)

        assert group_repo.get_by_id(group.group_id) is None

    def test_delete_nonexistent_does_nothing(
        self, group_repo: InMemoryGroupClaimRepository
    ) -> None:
        group_repo.delete(uuid4())  # should not raise

    # ── BaseRepo: get_by_ids ───────────────────────────────────────────────

    def test_get_by_ids_returns_matching(
        self, group_repo: InMemoryGroupClaimRepository
    ) -> None:
        g1 = _seed_group(group_repo)
        g2 = _seed_group(group_repo)
        g3 = _seed_group(group_repo)

        result = group_repo.get_by_ids([g1.group_id, g3.group_id])

        assert len(result) == 2
        assert g1 in result
        assert g3 in result
        assert g2 not in result

    def test_get_by_ids_returns_empty_when_none_match(
        self, group_repo: InMemoryGroupClaimRepository
    ) -> None:
        _seed_group(group_repo)
        result = group_repo.get_by_ids([uuid4(), uuid4()])
        assert result == []

    # ── GroupClaimRepoPort: get_by_group_name ───────────────────────────────

    def test_get_by_group_name_returns_group_when_found(
        self, group_repo: InMemoryGroupClaimRepository
    ) -> None:
        _seed_group(group_repo, name="Accidentes")

        result = group_repo.get_by_group_name("Accidentes")

        assert result is not None
        assert result.name == "Accidentes"

    def test_get_by_group_name_returns_none_when_not_found(
        self, group_repo: InMemoryGroupClaimRepository
    ) -> None:
        result = group_repo.get_by_group_name("Inexistente")
        assert result is None

    # ── GroupClaimRepoPort: get_by_text_like ───────────────────────────────

    def test_get_by_text_like_returns_matching(
        self, group_repo: InMemoryGroupClaimRepository
    ) -> None:
        _seed_group(group_repo, name="Accidentes")
        _seed_group(group_repo, name="Robo Total")
        _seed_group(group_repo, name="Accidentes Menores")

        result = group_repo.get_by_text_like("accidente")

        assert len(result) == 2
        names = {g.name for g in result}
        assert "Accidentes" in names
        assert "Accidentes Menores" in names

    def test_get_by_text_like_returns_empty_when_no_match(
        self, group_repo: InMemoryGroupClaimRepository
    ) -> None:
        _seed_group(group_repo, name="Robo Total")
        _seed_group(group_repo, name="Incendio")

        result = group_repo.get_by_text_like("xx")

        assert result == []

    # ── GroupClaimRepoPort: get_by_claim_id ────────────────────────────────

    def test_get_by_claim_id_returns_group_when_claim_has_group(
        self, group_repo_with_claims: InMemoryGroupClaimRepository
    ) -> None:
        group_id = uuid4()
        _seed_group(group_repo_with_claims, group_id=group_id, name="Mi Grupo")
        claim = Claim(
            claim_id=uuid4(),
            claim_kind_id=uuid4(),
            group_id=group_id,
            claimer_name="Test Claimer",
            policy_number="POL001",
            plate="ABC123",
        )
        group_repo_with_claims._claim_store.append(claim)

        result = group_repo_with_claims.get_by_claim_id(claim.claim_id)

        assert result is not None
        assert result.group_id == group_id
        assert result.name == "Mi Grupo"

    def test_get_by_claim_id_returns_none_when_claim_has_no_group(
        self, group_repo_with_claims: InMemoryGroupClaimRepository
    ) -> None:
        _seed_group(group_repo_with_claims, name="Grupo A")
        claim = Claim(
            claim_id=uuid4(),
            claim_kind_id=uuid4(),
            group_id=uuid4(),
            claimer_name="Test Claimer",
            policy_number="POL001",
            plate="ABC123",
        )
        group_repo_with_claims._claim_store.append(claim)

        result = group_repo_with_claims.get_by_claim_id(claim.claim_id)

        assert result is None

    def test_get_by_claim_id_returns_none_when_claim_does_not_exist(
        self, group_repo_with_claims: InMemoryGroupClaimRepository
    ) -> None:
        _seed_group(group_repo_with_claims, name="Grupo A")

        result = group_repo_with_claims.get_by_claim_id(uuid4())

        assert result is None

    # ── _DocReachable stubs ────────────────────────────────────────────────

    def test_get_by_document_id_returns_empty_list(
        self, group_repo: InMemoryGroupClaimRepository
    ) -> None:
        _seed_group(group_repo)
        result = group_repo.get_by_document_id(uuid4())
        assert result == []

    def test_get_by_document_returns_empty_list(
        self, group_repo: InMemoryGroupClaimRepository
    ) -> None:
        _seed_group(group_repo)
        result = group_repo.get_by_document(b"some content")
        assert result == []


# ═══════════════════════════════════════════════════════════════════════════════
# RegistrarGrupo Use Case Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestRegistrarGrupo:
    """Tests for RegistrarGrupo use case."""

    def test_creates_new_group(self, group_repo: InMemoryGroupClaimRepository) -> None:
        uc = RegistrarGrupo(group_repo)

        result = uc.execute("Nuevo Grupo")

        assert result is not None
        assert result.name == "Nuevo Grupo"
        assert group_repo.get_by_id(result.group_id) is not None

    def test_returns_existing_group_on_duplicate_name(
        self, group_repo: InMemoryGroupClaimRepository
    ) -> None:
        original = _seed_group(group_repo, name="Grupo A")
        uc = RegistrarGrupo(group_repo)

        result = uc.execute("Grupo A")

        assert result.group_id == original.group_id
        assert result.name == "Grupo A"
        # Verify only one group exists
        assert len(group_repo.get_all()) == 1


# ═══════════════════════════════════════════════════════════════════════════════
# ObtenerGrupos Use Case Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestObtenerGrupos:
    """Tests for ObtenerGrupos use case."""

    def test_get_all_returns_all_groups(
        self, group_repo: InMemoryGroupClaimRepository
    ) -> None:
        _seed_group(group_repo, name="Z Grupo")
        _seed_group(group_repo, name="A Grupo")
        uc = ObtenerGrupos(group_repo)

        result = uc.execute()

        assert len(result) == 2

    def test_get_all_returns_empty_when_no_groups(
        self, group_repo: InMemoryGroupClaimRepository
    ) -> None:
        uc = ObtenerGrupos(group_repo)

        result = uc.execute()

        assert result == []

    def test_buscar_por_texto_returns_matching(
        self, group_repo: InMemoryGroupClaimRepository
    ) -> None:
        _seed_group(group_repo, name="Accidentes")
        _seed_group(group_repo, name="Robo Total")
        _seed_group(group_repo, name="Accidentes Menores")
        uc = ObtenerGrupos(group_repo)

        result = uc.buscar_por_texto("accidente")

        assert len(result) == 2

    def test_buscar_por_texto_returns_empty_when_no_match(
        self, group_repo: InMemoryGroupClaimRepository
    ) -> None:
        _seed_group(group_repo, name="Robo Total")
        uc = ObtenerGrupos(group_repo)

        result = uc.buscar_por_texto("xx")

        assert result == []


# ═══════════════════════════════════════════════════════════════════════════════
# EliminarGrupo Use Case Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestEliminarGrupo:
    """Tests for EliminarGrupo use case."""

    def test_delete_group_with_no_claims(
        self, group_repo: InMemoryGroupClaimRepository, claim_repo
    ) -> None:
        group = _seed_group(group_repo)
        uc = EliminarGrupo(group_repo, claim_repo)

        result = uc.execute(group.group_id)

        assert result is True
        assert group_repo.get_by_id(group.group_id) is None

    def test_delete_nonexistent_group_returns_false(
        self, group_repo: InMemoryGroupClaimRepository, claim_repo
    ) -> None:
        uc = EliminarGrupo(group_repo, claim_repo)

        result = uc.execute(uuid4())

        assert result is False

    def test_delete_group_with_associated_claims_raises_error(
        self, group_repo: InMemoryGroupClaimRepository, claim_repo
    ) -> None:
        group_id = uuid4()
        _seed_group(group_repo, group_id=group_id)
        _seed_claim(claim_repo, group_id=group_id)
        uc = EliminarGrupo(group_repo, claim_repo)

        with pytest.raises(ValueError, match="tiene siniestros asociados"):
            uc.execute(group_id)

        # Group should still exist
        assert group_repo.get_by_id(group_id) is not None


# ═══════════════════════════════════════════════════════════════════════════════
# ActualizarGrupo Use Case Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestActualizarGrupo:
    """Tests for ActualizarGrupo use case."""

    def test_update_existing_group_name(
        self, group_repo: InMemoryGroupClaimRepository
    ) -> None:
        group = _seed_group(group_repo, name="Viejos")
        uc = ActualizarGrupo(group_repo)

        result = uc.execute(group.group_id, "Nuevos")

        assert result is not None
        assert result.name == "Nuevos"
        stored = group_repo.get_by_id(group.group_id)
        assert stored is not None
        assert stored.name == "Nuevos"

    def test_update_nonexistent_group_returns_none(
        self, group_repo: InMemoryGroupClaimRepository
    ) -> None:
        uc = ActualizarGrupo(group_repo)

        result = uc.execute(uuid4(), "Cualquier Nombre")

        assert result is None

    def test_update_to_duplicate_name_raises_error(
        self, group_repo: InMemoryGroupClaimRepository
    ) -> None:
        _seed_group(group_repo, name="Grupo A")
        group_b = _seed_group(group_repo, name="Grupo B")
        uc = ActualizarGrupo(group_repo)

        with pytest.raises(ValueError, match="Ya existe un grupo"):
            uc.execute(group_b.group_id, "Grupo A")
