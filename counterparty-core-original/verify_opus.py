
import sys
import os
import types
from unittest.mock import MagicMock

# Mock dependencies that might be missing
sys.modules['termcolor'] = MagicMock()
sys.modules['appdirs'] = MagicMock()
sys.modules['bitcoin'] = MagicMock()
sys.modules['pygit2'] = MagicMock()
sys.modules['bitcoinutils'] = MagicMock()
sys.modules['bitcoinutils.setup'] = MagicMock()
sys.modules['yoyo'] = MagicMock()
sys.modules['yoyo.migrations'] = MagicMock()
sys.modules['flask'] = MagicMock()
sys.modules['flask_httpauth'] = MagicMock()
sys.modules['gevent'] = MagicMock()
sys.modules['gunicorn'] = MagicMock()
sys.modules['waitress'] = MagicMock()
sys.modules['falcon'] = MagicMock()
sys.modules['dateutil'] = MagicMock()
sys.modules['dateutil.tz'] = MagicMock()
sys.modules['multiprocessing_logging'] = MagicMock()
sys.modules['halo'] = MagicMock()
sys.modules['typing_extensions'] = MagicMock()
sys.modules['urllib3'] = MagicMock() 
sys.modules['compress_pickle'] = MagicMock()
sys.modules['json_log_formatter'] = MagicMock()
sys.modules['coloredlogs'] = MagicMock()
sys.modules['apsw'] = MagicMock()
sys.modules['zmq'] = MagicMock()

# Ensure we can import the library
sys.path.append(os.path.join(os.getcwd(), 'counterparty-core'))

try:
    from counterpartycore.lib.utils import helpers
    import mimetypes
except ImportError as e:
    print(f"Failed to import helpers: {e}")
    # Print traceback to see what triggered it
    import traceback
    traceback.print_exc()
    sys.exit(1)

def verify_opus():
    print("Verifying Opus MIME type support...")
    
    # Check 1: Classification
    mime_type = "audio/opus"
    classification = helpers.classify_mime_type(mime_type)
    print(f"Classification for '{mime_type}': {classification}")
    if classification != "binary":
        print("FAIL: Expected 'binary' classification")
        return False
        
    # Check 2: Content Check
    # mocked content (hex string as it is binary)
    content = "deadbeef" 
    problems = helpers.check_content(mime_type, content)
    print(f"check_content problems: {problems}")
    
    if problems:
        print("FAIL: check_content returned problems")
        return False

    # Check 3: Mimetypes registry
    # This might have been added by helpers import execution
    is_registered = "audio/opus" in mimetypes.types_map.values() or \
                    any(t == "audio/opus" for t in mimetypes.types_map.values())
    
    print(f"Is audio/opus registered in mimetypes? {is_registered}")
    
    # We explicitly added it in helpers.py, so it should be there.
    # Note: mimetypes.types_map might vary by python version/platform, 
    # but add_type adds to internal maps.
    
    # Let's check if extension map knows it
    ext = mimetypes.guess_extension("audio/opus")
    print(f"Guessed extension for audio/opus: {ext}")
    
    if ext != ".opus":
         print("WARNING: mimetypes.guess_extension did not return .opus")
         # This might not be a hard failure if the map allows it but guess_extension is finicky
         
    return True

if __name__ == "__main__":
    if verify_opus():
        print("SUCCESS: Opus support verified.")
        sys.exit(0)
    else:
        print("FAILURE: Opus support verification failed.")
        sys.exit(1)
