from src.models.voice_vasc_model import VoiceVascEstimator


def test_voxvasc_missing_pitch_is_unavailable():
    score, note = VoiceVascEstimator().score(None)
    assert score is None
    assert "unavailable" in note.lower()


def test_voxvasc_index_is_bounded_and_non_diagnostic():
    score, note = VoiceVascEstimator().score(180.0, 30.0)
    assert score is not None
    assert 0.0 <= score <= 100.0
    assert "not a hormone measurement" in note.lower()
    assert "not clinically validated" in note.lower()
