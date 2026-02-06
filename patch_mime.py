"""
Patch counterparty helpers.py to support MIME types with parameters.
Applies the fix from PR #3266: https://github.com/CounterpartyXCP/counterparty-core/pull/3266

Changes:
- classify_mime_type(): extract base MIME type before checking
- check_content(): extract base MIME type before validating against mimetypes lib
"""
import glob
import re
import sys

# Find helpers.py in the installed packages
pattern = "/venv/lib/python*/site-packages/counterpartycore/lib/utils/helpers.py"
matches = glob.glob(pattern)

if not matches:
    print(f"ERROR: Could not find helpers.py matching {pattern}")
    sys.exit(1)

filepath = matches[0]
print(f"Patching: {filepath}")

with open(filepath, "r") as f:
    content = f.read()

# --- Patch 1: classify_mime_type ---
# Add base_mime_type extraction and use it for all checks
old_classify = '''def classify_mime_type(mime_type):
    # Types that start with "text/" are textual
    if (
        mime_type.startswith("text/")
        or mime_type.startswith("message/")
        or mime_type.endswith("+xml")
    ):
        return "text"

    # List of application types that are textual
    if mime_type in ['''

new_classify = '''def classify_mime_type(mime_type):
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
    if base_mime_type in ['''

if old_classify in content:
    content = content.replace(old_classify, new_classify)
    print("  [OK] Patched classify_mime_type()")
else:
    # Check if already patched
    if "base_mime_type = mime_type.split" in content and "def classify_mime_type" in content:
        print("  [SKIP] classify_mime_type() already patched")
    else:
        print("  [WARN] Could not find classify_mime_type() pattern - attempting regex patch")
        # Fallback: regex-based patch
        content = re.sub(
            r'(def classify_mime_type\(mime_type\):)\n(\s+# Types)',
            r'\1\n    # Extract base MIME type (remove parameters like codecs)\n    base_mime_type = mime_type.split(";")[0].strip()\n\n\2',
            content
        )
        content = content.replace('mime_type.startswith("text/")', 'base_mime_type.startswith("text/")')
        content = content.replace('mime_type.startswith("message/")', 'base_mime_type.startswith("message/")')
        content = content.replace('mime_type.endswith("+xml")', 'base_mime_type.endswith("+xml")')
        # Only replace the "mime_type in [" inside classify_mime_type, not elsewhere
        content = re.sub(
            r'(# List of application types that are textual\n\s+if )mime_type( in \[)',
            r'\1base_mime_type\2',
            content
        )
        print("  [OK] Applied regex fallback for classify_mime_type()")

# --- Patch 2: Register missing MIME types in Python's mimetypes lib ---
# Alpine's Python is missing audio/ogg, video/ogg, etc.
# Add mimetypes.add_type() calls right after the existing `import mimetypes` line
if "import mimetypes" in content and "mimetypes.add_type" not in content:
    content = content.replace(
        "import mimetypes",
        "import mimetypes\n\n"
        "# Register MIME types missing from Alpine's Python\n"
        "mimetypes.add_type('audio/ogg', '.ogg')\n"
        "mimetypes.add_type('video/ogg', '.ogv')\n"
        "mimetypes.add_type('application/ogg', '.ogx')\n"
        "mimetypes.add_type('audio/flac', '.flac')\n"
        "mimetypes.add_type('audio/webm', '.weba')\n"
        "mimetypes.add_type('video/webm', '.webm')\n"
        "mimetypes.add_type('audio/mp4', '.m4a')\n"
        "mimetypes.add_type('video/mp4', '.mp4')",
        1  # only replace the first occurrence
    )
    print("  [OK] Registered missing MIME types (audio/ogg, video/ogg, etc.)")
else:
    if "mimetypes.add_type" in content:
        print("  [SKIP] MIME types already registered")
    else:
        print("  [WARN] Could not find 'import mimetypes' to add type registrations")

# --- Patch 3: Force User-Agent to avoid 403 Forbidden on Public Nodes ---
# Many public endpoints like PublicNode.com block default Python/Requests user agents.
# We inject a global default header update.
if "import requests" in content and "User-Agent" not in content:
    content = content.replace(
        "import requests",
        "import requests\n"
        "# Force Browser User-Agent to bypass public RPC blocks\n"
        "requests.utils.default_headers()['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'",
        1
    )
    print("  [OK] Patched Global User-Agent")
elif "import requests" not in content:
     # If requests isn't imported in helpers.py, import it just for this config
     content = "import requests\n# Force Browser User-Agent to bypass public RPC blocks\nrequests.utils.default_headers()['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'\n" + content
     print("  [OK] Injected Global User-Agent (ignoring missing import)")

# --- Patch 4: check_content ---
old_check = '    content_mime_type = mime_type or "text/plain"\n    if content_mime_type not in mimetypes.types_map.values():'
new_check = '    content_mime_type = mime_type or "text/plain"\n    # Extract base MIME type (remove parameters like codecs)\n    base_mime_type = content_mime_type.split(";")[0].strip()\n    if base_mime_type not in mimetypes.types_map.values():'

if old_check in content:
    content = content.replace(old_check, new_check)
    print("  [OK] Patched check_content()")
else:
    if 'base_mime_type = content_mime_type.split(";")' in content:
        print("  [SKIP] check_content() already patched")
    else:
        print("  [WARN] Could not find check_content() exact pattern - attempting regex patch")
        content = re.sub(
            r'(content_mime_type = mime_type or "text/plain"\n)(\s+if )(content_mime_type)( not in mimetypes\.types_map\.values\(\):)',
            r'\1    # Extract base MIME type (remove parameters like codecs)\n    base_mime_type = content_mime_type.split(";")[0].strip()\n\2base_mime_type\4',
            content
        )
        print("  [OK] Applied regex fallback for check_content()")

        print("  [OK] Applied regex fallback for check_content()")

with open(filepath, "w") as f:
    f.write(content)

# --- Patch 5: Increase Waitress Body Size Limit in wsgi.py ---
# The WSGI server instantiation hardcodes params and ignores config file limits.
# We must patch the python code directly to allow large uploads (e.g. 7MB hex strings).

wsgi_pattern = "/venv/lib/python*/site-packages/counterpartycore/lib/api/wsgi.py"
wsgi_matches = glob.glob(wsgi_pattern)

if wsgi_matches:
    wsgi_filepath = wsgi_matches[0]
    print(f"Patching: {wsgi_filepath}")
    
    with open(wsgi_filepath, "r") as f:
        wsgi_content = f.read()

    # Look for the waitress creation call
    target_str = "threads=config.WAITRESS_THREADS"
    replacement_str = "threads=config.WAITRESS_THREADS, max_request_body_size=50000000"

    if target_str in wsgi_content and "max_request_body_size" not in wsgi_content:
        wsgi_content = wsgi_content.replace(target_str, replacement_str)
        with open(wsgi_filepath, "w") as f:
            f.write(wsgi_content)
        print("  [OK] Patched wsgi.py: Increased max_request_body_size to 50MB")
    elif "max_request_body_size" in wsgi_content:
        print("  [SKIP] wsgi.py already patched with max_request_body_size")
    else:
        print("  [WARN] Could not find 'threads=config.WAITRESS_THREADS' in wsgi.py")
else:
    print(f"  [WARN] Could not find wsgi.py matching {wsgi_pattern}")

# --- Patch 6: Increase Flask/Werkzeug max_form_memory_size in apiserver.py ---
# Werkzeug's Request class defaults max_form_memory_size to 500KB.
# When parsing URL-encoded form data (e.g. hex-encoded audio files in the
# description field), content_length > 500KB triggers a 413 RequestEntityTooLarge
# BEFORE our route handler even runs. We must increase this limit.

api_pattern = "/venv/lib/python*/site-packages/counterpartycore/lib/api/apiserver.py"
api_matches = glob.glob(api_pattern)

if api_matches:
    api_filepath = api_matches[0]
    print(f"Patching: {api_filepath}")

    with open(api_filepath, "r") as f:
        api_content = f.read()

    # Insert max_form_memory_size override right after the Flask app is created.
    # Werkzeug's Request.max_form_memory_size is a class attribute (default 500KB),
    # NOT read from Flask config. We must set it on the request class directly.
    target_api = 'app = Flask(config.APP_NAME)'
    replacement_api = (
        'app = Flask(config.APP_NAME)\n'
        '    # Increase form data memory limit from 500KB default to 50MB\n'
        '    # Required for large hex-encoded inscription data in URL-encoded POST bodies\n'
        '    app.request_class.max_form_memory_size = 50_000_000'
    )

    if target_api in api_content and "max_form_memory_size" not in api_content:
        api_content = api_content.replace(target_api, replacement_api)
        with open(api_filepath, "w") as f:
            f.write(api_content)
        print("  [OK] Patched apiserver.py: Increased max_form_memory_size to 50MB")
    elif "max_form_memory_size" in api_content:
        print("  [SKIP] apiserver.py already patched with max_form_memory_size")
    else:
        print("  [WARN] Could not find Flask app creation in apiserver.py")
else:
    print(f"  [WARN] Could not find apiserver.py matching {api_pattern}")

print("Patch complete!")
