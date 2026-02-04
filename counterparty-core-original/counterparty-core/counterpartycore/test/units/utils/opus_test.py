
import pytest
from counterpartycore.lib.utils import helpers

def test_opus_mime_type_support():
    """Test that audio/opus is correctly recognized and handled."""
    # Test classification (audio is considered binary by default if not text)
    assert helpers.classify_mime_type("audio/opus") == "binary"
    
    # Test valid opus content check
    # We just need to ensure check_content doesn't return "Invalid mime type"
    # mimetypes.add_type should make it valid if it wasn't already.
    
    # Normally check_content checks against mimetypes.types_map.values()
    # Let's verify our addition worked.
    problems = helpers.check_content("audio/opus", "somedata")
    
    # If it was invalid, problems would contain "Invalid mime type: audio/opus"
    # We expect no problems related to the mime type validity itself.
    # Note: "somedata" is odd-length string, so it might fail hex conversion if treated as binary
    # helpers.content_to_bytes will try to unhexlify if binary.
    
    # Real opus data would be binary bytes. content_to_bytes expects hex string for binary types?
    # Let's look at content_to_bytes implementation again.
    # if file_type == "text": return content.encode("utf-8")
    # else: return binascii.unhexlify(content)
    
    # So for audio/opus (binary), content should be hex string.
    valid_hex_content = "deadbeef"
    problems = helpers.check_content("audio/opus", valid_hex_content)
    assert problems == []

    # Verify that it was indeed added to mimetypes (implicit in check_content success, but good to be explicit)
    import mimetypes
    assert "audio/opus" in mimetypes.types_map.values() or \
           any(type == "audio/opus" for type in mimetypes.types_map.values()) or \
           (mimetypes.guess_extension("audio/opus") == ".opus")


def test_ogg_mime_type_support():
    """Test that audio/ogg is correctly recognized and handled."""
    # Test classification
    assert helpers.classify_mime_type("audio/ogg") == "binary"
    
    # Test valid ogg content check with hex data
    valid_hex_content = "4f676753"  # "OggS" magic number in hex
    problems = helpers.check_content("audio/ogg", valid_hex_content)
    assert problems == []
    
    # Verify registration
    import mimetypes
    assert "audio/ogg" in mimetypes.types_map.values() or \
           any(type == "audio/ogg" for type in mimetypes.types_map.values()) or \
           (mimetypes.guess_extension("audio/ogg") == ".ogg")


def test_ogg_opus_with_codec_parameter():
    """Test that audio/ogg;codecs=opus (with codec parameter) is correctly handled."""
    # This is the key test for PR #3266
    # The check_content function should extract base MIME type before validation
    
    # Test classification with codec parameter
    assert helpers.classify_mime_type("audio/ogg;codecs=opus") == "binary"
    
    # Test valid content check with codec parameter
    valid_hex_content = "4f676753"  # "OggS" magic number in hex
    problems = helpers.check_content("audio/ogg;codecs=opus", valid_hex_content)
    assert problems == []
    
    # Test with different codec parameters
    problems = helpers.check_content("audio/ogg; codecs=opus", valid_hex_content)
    assert problems == []
    
    problems = helpers.check_content("audio/ogg;codecs=vorbis", valid_hex_content)
    assert problems == []
