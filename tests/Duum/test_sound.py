from games.Duum.src.sound import SoundManager


def test_sound_manager_files():
    """Test that Duum sound files are correctly configured."""
    files = SoundManager.SOUND_FILES
    assert "shoot" in files
    assert "beast" in files
    assert "music_intro" in files
    assert len(files) > 10
