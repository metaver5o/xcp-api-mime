
import mimetypes
import decimal

# Replicating the logic from helpers.py to verify it works as expected

# The change we made in helpers.py
mimetypes.add_type('audio/opus', '.opus')

def classify_mime_type(mime_type):
    # Extract base MIME type (remove parameters like codecs)
    base_mime_type = mime_type.split(";")[0].strip()

    # Types that start with "text/" are textual
    if (
        base_mime_type.startswith("text/")
        or base_mime_type.startswith("message/")
        or base_mime_type.endswith("+xml")
    ):
        return "text"

    # List of application types that are textual
    if base_mime_type in [
        "application/xml",
        "application/javascript",
        "application/json",
        "application/manifest+json",
        "application/x-python-code",
        "application/x-sh",
        "application/x-csh",
        "application/x-tex",
        "application/x-latex",
    ]:
        return "text"

    # By default, consider the MIME type as binary
    return "binary"

def verify_logic():
    print("Verifying Opus logic...")
    
    # 1. Verify mimetypes.add_type worked
    if "audio/opus" not in mimetypes.types_map.values():
        # It might be in common_types or elsewhere depending on python version
        # but check_content logic uses mimetypes.types_map.values()
        # so we MUST ensure it appears there.
        # However, types_map is deprecated in 3.8+ and replaced by knownfiles etc? 
        # helpers.py explicitly uses: if base_mime_type not in mimetypes.types_map.values():
        
        # In Python 3, types_map might be empty if not initialized or behave differently?
        # Let's check what mimetypes.types_map contains.
        pass

    # Replicate check_content logic part
    base_mime_type = "audio/opus"
    
    # Explicit check used in helpers.py
    known_types = mimetypes.types_map.values()
    if base_mime_type in known_types:
        print("SUCCESS: audio/opus found in mimetypes.types_map.values()")
    else:
        # On some systems/python versions types_map might not be fully populated with add_type?
        # Let's explicitly check if add_type adds to types_map.
        # According to valid sources, add_type adds to internal db. types_map is a legacy dictionary.
        # In Python 3.7+, types_map references encodings_map/suffix_map etc?
        # Actually helpers.py code might be using a legacy attribute which works because standard lib maintains it?
        # Let's print the result.
        print(f"WARNING: audio/opus NOT found in mimetypes.types_map.values(). Size of map: {len(known_types)}")
        
        # If helpers.py uses mimetypes.types_map.values(), and it's missing, then helpers.py is broken for custom types?
        # Let's check if there is an alternative check.
        # But wait, I added it via mimetypes.add_type.
        pass

    # 2. Verify classification
    classification = classify_mime_type("audio/opus")
    print(f"Classification: {classification}")
    if classification == "binary":
        print("SUCCESS: Classified as binary")
    else:
        print("FAIL: Classified as text")
        return False

    return True

if __name__ == "__main__":
    verify_logic()
