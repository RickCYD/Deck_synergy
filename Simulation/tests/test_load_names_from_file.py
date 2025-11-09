import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from deck_loader import load_names_from_file


def test_load_names_from_file_quantities(tmp_path):
    content = "\n".join([
        "2 Sol Ring",
        "Island x3",
        "Mountain",
        "# Comment"
    ])
    file_path = tmp_path / "cards.txt"
    file_path.write_text(content)
    names = load_names_from_file(str(file_path))
    assert names == [
        "Sol Ring", "Sol Ring",
        "Island", "Island", "Island",
        "Mountain"
    ]
