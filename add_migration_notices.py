#!/usr/bin/env python3
"""
Quick script to add migration notices to all extractor files.
"""

import os
import re

MIGRATION_NOTICE = '''
MIGRATION NOTICE:
==================
This module uses legacy regex-based extraction. For new code, consider using
the unified parser instead:

    from src.core.card_parser import UnifiedCardParser
    parser = UnifiedCardParser()
    abilities = parser.parse_card(card)

See UNIFIED_ARCHITECTURE_GUIDE.md for details.

The functions in this file are maintained for backward compatibility.
'''

IMPORT_ADDITIONS = '''
# Optional: Import unified parser for recommended path
try:
    from src.core.card_parser import UnifiedCardParser
    _UNIFIED_PARSER_AVAILABLE = True
except ImportError:
    _UNIFIED_PARSER_AVAILABLE = False
'''

def add_migration_notice_to_file(file_path):
    """Add migration notice to a single extractor file."""
    print(f"Processing: {file_path}")

    with open(file_path, 'r') as f:
        content = f.read()

    # Check if already has migration notice
    if 'MIGRATION NOTICE' in content:
        print(f"  ✓ Already has migration notice")
        return False

    # Find the end of the docstring
    docstring_pattern = r'("""[\s\S]*?""")'
    match = re.search(docstring_pattern, content)

    if not match:
        print(f"  ✗ No docstring found, skipping")
        return False

    # Insert migration notice before closing """
    old_docstring = match.group(1)
    new_docstring = old_docstring.replace('"""', f'\n{MIGRATION_NOTICE}\n"""', 1)
    new_docstring = new_docstring.replace('"""', '"""', 1)  # Only first occurrence changed

    content = content.replace(old_docstring, new_docstring)

    # Add import additions after initial imports
    import_pattern = r'(import\s+\w+\n(?:import\s+\w+\n|from\s+.*?\n)*)'
    import_match = re.search(import_pattern, content)

    if import_match and '_UNIFIED_PARSER_AVAILABLE' not in content:
        # Insert after imports but add warnings import if needed
        if 'import warnings' not in content:
            content = content.replace(
                import_match.group(0),
                import_match.group(0) + '\nimport warnings\n' + IMPORT_ADDITIONS
            )
        else:
            content = content.replace(
                import_match.group(0),
                import_match.group(0) + '\n' + IMPORT_ADDITIONS
            )

    with open(file_path, 'w') as f:
        f.write(content)

    print(f"  ✓ Added migration notice")
    return True

def main():
    """Add migration notices to all extractor files."""
    extractor_files = [
        'src/utils/protection_extractors.py',
        'src/utils/mana_extractors.py',
        'src/utils/combat_extractors.py',
        'src/utils/damage_extractors.py',
        'src/utils/ramp_extractors.py',
        'src/utils/removal_extractors.py',
        'src/utils/recursion_extractors.py',
        'src/utils/keyword_extractors.py',
        'src/utils/graveyard_extractors.py',
        'src/utils/card_advantage_extractors.py',
        'src/utils/boardwipe_extractors.py',
        'src/utils/tribal_extractors.py',
        'src/utils/etb_extractors.py',
    ]

    updated_count = 0
    for file_path in extractor_files:
        full_path = os.path.join('/home/user/Deck_synergy', file_path)
        if os.path.exists(full_path):
            if add_migration_notice_to_file(full_path):
                updated_count += 1
        else:
            print(f"  ✗ File not found: {full_path}")

    print(f"\n✅ Updated {updated_count} files")

if __name__ == '__main__':
    main()
