
import unittest

def clean_names(source_str, blacklist_set):
    """
    Splits source_str by comma, strips whitespace, filters out names in blacklist_set,
    and rejoins the result.
    Case-insensitive matching for blacklist.
    """
    if not source_str or not isinstance(source_str, str):
        return ""
    
    # Normalize blacklist to lowercase for case-insensitive comparison
    blacklist_lower = {name.lower().strip() for name in blacklist_set}
    
    names = source_str.split(',')
    cleaned_names = []
    
    for name in names:
        name_clean = name.strip()
        if not name_clean:
            continue
        if name_clean.lower() not in blacklist_lower:
            cleaned_names.append(name_clean)
            
    return ", ".join(cleaned_names)

class TestCleaningLogic(unittest.TestCase):
    def test_basic_removal(self):
        self.assertEqual(clean_names("john,mark", {"john"}), "mark")

    def test_middle_removal(self):
        self.assertEqual(clean_names("alice, bob, charlie", {"bob"}), "alice, charlie")

    def test_full_removal(self):
        self.assertEqual(clean_names("single_name", {"single_name"}), "")

    def test_case_insensitivity(self):
        self.assertEqual(clean_names("John,Mark", {"john"}), "Mark")
        
    def test_whitespace_handling(self):
        self.assertEqual(clean_names(" alice , bob ", {"bob"}), "alice")

    def test_empty_string(self):
        self.assertEqual(clean_names("", {"john"}), "")
        
    def test_no_matches(self):
        self.assertEqual(clean_names("alice,bob", {"charlie"}), "alice, bob")

if __name__ == '__main__':
    unittest.main()
