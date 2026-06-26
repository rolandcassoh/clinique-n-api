"""Tests unitaires — domaine clinic (logique pure, sans I/O)."""
from datetime import date, datetime, time, timezone
from unittest.mock import AsyncMock

import pytest

from app.modules.clinic.application.cas_utilisation import GetAvailableSlotsUseCase
from app.modules.clinic.domain.entites import DoctorLeave, DoctorSession, TimeSlot


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_session(
    doctor_id: int = 1,
    day_of_week: int = 0,  # Lundi
    start_time: time = time(9, 0),
    end_time: time = time(12, 0),
    slot_duration_minutes: int = 30,
    max_patients_per_slot: int = 1,
) -> DoctorSession:
    return DoctorSession(
        id=1,
        doctor_id=doctor_id,
        day_of_week=day_of_week,
        start_time=start_time,
        end_time=end_time,
        slot_duration_minutes=slot_duration_minutes,
        max_patients_per_slot=max_patients_per_slot,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


def _make_leave(
    doctor_id: int = 1,
    leave_date: date = date(2025, 6, 2),
    is_full_day: bool = True,
) -> DoctorLeave:
    return DoctorLeave(
        id=1, doctor_id=doctor_id, leave_date=leave_date,
        reason="congé", is_full_day=is_full_day,
        start_time=None, end_time=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


# ── DoctorSession.generate_theoretical_slots ─────────────────────────────────

class TestGenerateTheoreticalSlots:
    def test_genere_6_creneaux_30min_sur_3h(self) -> None:
        session = _make_session(start_time=time(9, 0), end_time=time(12, 0), slot_duration_minutes=30)
        # 9h → 11h30 (dernier slot qui finit ≤ 12h)
        slots = session.generate_theoretical_slots(date(2025, 6, 2))
        assert len(slots) == 6
        assert slots[0].hour == 9 and slots[0].minute == 0
        assert slots[-1].hour == 11 and slots[-1].minute == 30

    def test_genere_creneaux_60min(self) -> None:
        session = _make_session(
            start_time=time(8, 0), end_time=time(17, 0), slot_duration_minutes=60
        )
        slots = session.generate_theoretical_slots(date(2025, 6, 2))
        assert len(slots) == 9  # 8h, 9h, ..., 16h

    def test_creneaux_vides_si_duree_trop_longue(self) -> None:
        # end_time - start_time < slot_duration → aucun créneau
        session = _make_session(
            start_time=time(9, 0), end_time=time(9, 20), slot_duration_minutes=30
        )
        slots = session.generate_theoretical_slots(date(2025, 6, 2))
        assert slots == []

    def test_date_correcte_dans_les_slots(self) -> None:
        session = _make_session(start_time=time(10, 0), end_time=time(11, 0), slot_duration_minutes=60)
        target_date = date(2025, 12, 25)
        slots = session.generate_theoretical_slots(target_date)
        assert len(slots) == 1
        assert slots[0].date() == target_date


# ── TimeSlot.overlaps ─────────────────────────────────────────────────────────

class TestTimeSlotOverlaps:
    def _dt(self, h: int, m: int = 0) -> datetime:
        return datetime(2025, 6, 2, h, m)

    def test_chevauchement_partiel(self) -> None:
        a = TimeSlot(start=self._dt(9), end=self._dt(10))
        b = TimeSlot(start=self._dt(9, 30), end=self._dt(10, 30))
        assert a.overlaps(b) is True
        assert b.overlaps(a) is True

    def test_pas_de_chevauchement_consecutifs(self) -> None:
        a = TimeSlot(start=self._dt(9), end=self._dt(10))
        b = TimeSlot(start=self._dt(10), end=self._dt(11))
        assert a.overlaps(b) is False

    def test_pas_de_chevauchement_disjoints(self) -> None:
        a = TimeSlot(start=self._dt(9), end=self._dt(10))
        b = TimeSlot(start=self._dt(11), end=self._dt(12))
        assert a.overlaps(b) is False

    def test_chevauchement_inclusion_totale(self) -> None:
        outer = TimeSlot(start=self._dt(8), end=self._dt(18))
        inner = TimeSlot(start=self._dt(10), end=self._dt(11))
        assert outer.overlaps(inner) is True

    def test_chevauchement_meme_creneau(self) -> None:
        a = TimeSlot(start=self._dt(9), end=self._dt(10))
        b = TimeSlot(start=self._dt(9), end=self._dt(10))
        assert a.overlaps(b) is True


# ── GetAvailableSlotsUseCase ──────────────────────────────────────────────────

class TestGetAvailableSlotsUseCase:
    @pytest.mark.asyncio
    async def test_date_passee_retourne_vide(self) -> None:
        repo = AsyncMock()
        uc = GetAvailableSlotsUseCase(repo)
        # 2020 est clairement dans le passé
        result = await uc.execute(doctor_id=1, for_date=date(2020, 1, 1))
        assert result == []

    @pytest.mark.asyncio
    async def test_pas_de_session_retourne_vide(self) -> None:
        repo = AsyncMock()
        repo.find_active_session.return_value = None
        uc = GetAvailableSlotsUseCase(repo)
        result = await uc.execute(doctor_id=1, for_date=date(2030, 6, 2))
        assert result == []

    @pytest.mark.asyncio
    async def test_conge_plein_jour_retourne_vide(self) -> None:
        repo = AsyncMock()
        target_date = date(2030, 6, 2)  # lundi
        # day_of_week = 0 (lundi) en Python
        session = _make_session(day_of_week=target_date.weekday())
        repo.find_active_session.return_value = session
        repo.find_leave.return_value = _make_leave(leave_date=target_date, is_full_day=True)

        uc = GetAvailableSlotsUseCase(repo)
        result = await uc.execute(doctor_id=1, for_date=target_date)
        assert result == []

    @pytest.mark.asyncio
    async def test_creneaux_disponibles_retournes(self) -> None:
        repo = AsyncMock()
        # 2030-06-03 = lundi (weekday=0)
        target_date = date(2030, 6, 3)
        session = _make_session(
            day_of_week=target_date.weekday(),
            start_time=time(9, 0),
            end_time=time(11, 0),
            slot_duration_minutes=60,
            max_patients_per_slot=2,
        )
        repo.find_active_session.return_value = session
        repo.find_leave.return_value = None
        repo.count_booked_slots.return_value = {}  # aucun RDV bookédé

        uc = GetAvailableSlotsUseCase(repo)
        result = await uc.execute(doctor_id=1, for_date=target_date)
        # 9h et 10h → 2 créneaux
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_creneaux_complets_exclus(self) -> None:
        """Un créneau avec booked_count >= max_patients_per_slot est exclu."""
        repo = AsyncMock()
        target_date = date(2030, 6, 3)
        session = _make_session(
            day_of_week=target_date.weekday(),
            start_time=time(9, 0),
            end_time=time(11, 0),
            slot_duration_minutes=60,
            max_patients_per_slot=1,
        )
        repo.find_active_session.return_value = session
        repo.find_leave.return_value = None

        # Le créneau 9h est complet (1 RDV déjà), 10h est libre
        slot_9h = datetime(2030, 6, 3, 9, 0)
        repo.count_booked_slots.return_value = {slot_9h.isoformat(): 1}

        uc = GetAvailableSlotsUseCase(repo)
        result = await uc.execute(doctor_id=1, for_date=target_date)
        # Seul 10h devrait rester
        assert len(result) == 1
        assert result[0].hour == 10
