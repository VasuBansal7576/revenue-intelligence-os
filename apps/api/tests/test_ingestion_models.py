import pytest
from pydantic import ValidationError

from app.ingestion.models import ChampionSignal


def test_champion_signal_rejects_unknown_signal_type() -> None:
    with pytest.raises(ValidationError):
        ChampionSignal(contact_id="contact_elena", signal_type="renegade", evidence_quote="No reply.")
