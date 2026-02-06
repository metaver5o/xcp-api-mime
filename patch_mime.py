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

# --- Patch 3: check_content ---
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

with open(filepath, "w") as f:
    f.write(content)

print("Patch complete!")
