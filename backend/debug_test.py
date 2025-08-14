"""Debug test to identify the issue"""

import re


def test_name_cleaning():
    """Test name cleaning logic"""

    def clean_name(name: str) -> str:
        """Clean name string"""
        if not name:
            return ""

        # Remove parentheses and contents, keep Chinese, English, and · symbol
        name_clean_pattern = re.compile(r"[^\u4e00-\u9fff\u0041-\u005a\u0061-\u007a·]")
        cleaned = name_clean_pattern.sub("", name.strip())
        return cleaned.lower()

    try:
        # Test cases
        result1 = clean_name("张三（技术员）")
        print(f"Test 1: '张三（技术员）' -> '{result1}'")

        result2 = clean_name("李四 [组长]")
        print(f"Test 2: '李四 [组长]' -> '{result2}'")

        result3 = clean_name("王五·赵六")
        print(f"Test 3: '王五·赵六' -> '{result3}'")

        result4 = clean_name("John Smith")
        print(f"Test 4: 'John Smith' -> '{result4}'")

        print("✓ Name cleaning tests completed")
        return True
    except Exception as e:
        print(f"Error in name cleaning: {e}")
        return False


if __name__ == "__main__":
    test_name_cleaning()
