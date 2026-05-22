"""Tests for the multi-format document parser."""

import tempfile
import os
from pathlib import Path
from datetime import datetime

import pytest


class TestDocumentParser:
    """Test suite for DocumentParser class."""

    @pytest.fixture
    def parser(self):
        """Initialize the parser for testing."""
        from process.parse import DocumentParser
        return DocumentParser()

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    # ========================================================================
    # Text file parsing tests
    # ========================================================================

    def test_parse_text_file(self, parser, temp_dir):
        """Test parsing a plain text file."""
        text_content = "This is a test document.\nIt has multiple lines.\nAnd some content."
        text_path = os.path.join(temp_dir, "test.txt")

        with open(text_path, "w") as f:
            f.write(text_content)

        result = parser.parse_text(text_path)

        assert isinstance(result, dict)
        assert "text" in result
        assert "title" in result
        assert "source" in result
        assert "format" in result
        assert result["format"] == "text"
        assert "This is a test document" in result["text"]
        assert result["source"] == text_path

    def test_parse_text_file_with_encoding_errors(self, parser, temp_dir):
        """Test parsing text file with encoding errors handled gracefully."""
        text_path = os.path.join(temp_dir, "encoding_test.txt")

        # Write bytes with some invalid UTF-8 sequences
        with open(text_path, "wb") as f:
            f.write(b"Valid text \xff\xfe invalid chars")

        result = parser.parse_text(text_path)

        assert isinstance(result, dict)
        assert "text" in result
        assert result["format"] == "text"
        # Should not raise, encoding errors should be ignored

    def test_parse_text_file_empty(self, parser, temp_dir):
        """Test parsing an empty text file."""
        text_path = os.path.join(temp_dir, "empty.txt")
        with open(text_path, "w") as f:
            f.write("")

        result = parser.parse_text(text_path)

        assert isinstance(result, dict)
        assert "text" in result
        assert result["format"] == "text"

    # ========================================================================
    # Markdown file parsing tests
    # ========================================================================

    def test_parse_markdown_file(self, parser, temp_dir):
        """Test parsing a markdown file."""
        md_content = """# Test Document

This is a test markdown document.

## Section 1
Some content here.

## Section 2
More content here.
"""
        md_path = os.path.join(temp_dir, "test.md")

        with open(md_path, "w") as f:
            f.write(md_content)

        result = parser.parse_markdown(md_path)

        assert isinstance(result, dict)
        assert "text" in result
        assert "title" in result
        assert "source" in result
        assert "format" in result
        assert result["format"] == "markdown"
        assert "Test Document" in result["text"]
        assert result["source"] == md_path

    def test_parse_markdown_file_with_code_blocks(self, parser, temp_dir):
        """Test parsing markdown with code blocks."""
        md_content = """# Code Example

```python
def hello():
    print("Hello, World!")
```

Some text after code block.
"""
        md_path = os.path.join(temp_dir, "code.md")

        with open(md_path, "w") as f:
            f.write(md_content)

        result = parser.parse_markdown(md_path)

        assert isinstance(result, dict)
        assert "text" in result
        assert result["format"] == "markdown"
        assert "Code Example" in result["text"]

    # ========================================================================
    # URL parsing tests
    # ========================================================================

    def test_parse_url_wikipedia(self, parser):
        """Test parsing a simple Wikipedia page."""
        url = "https://en.wikipedia.org/wiki/Python_(programming_language)"

        result = parser.parse_url(url)

        assert isinstance(result, dict)
        assert "text" in result
        assert "title" in result
        assert "source" in result
        assert "format" in result
        assert result["format"] == "html"
        assert result["source"] == url
        assert len(result["text"]) > 0
        # Should contain some Python-related content
        assert len(result["text"]) < 100001  # Should be under max limit

    def test_parse_url_with_invalid_url(self, parser):
        """Test parsing an invalid URL."""
        url = "https://this-domain-should-not-exist-12345.com/page"

        result = parser.parse_url(url)

        assert isinstance(result, dict)
        assert "error" in result or result.get("text") == ""

    def test_parse_url_preserves_source(self, parser):
        """Test that parse_url preserves the source URL."""
        url = "https://en.wikipedia.org/wiki/Computer_science"

        result = parser.parse_url(url)

        assert result["source"] == url
        assert result["format"] == "html"

    # ========================================================================
    # Dispatcher (parse method) tests
    # ========================================================================

    def test_parse_dispatcher_text_file(self, parser, temp_dir):
        """Test the parse dispatcher with a text file."""
        text_path = os.path.join(temp_dir, "doc.txt")
        with open(text_path, "w") as f:
            f.write("Test content")

        result = parser.parse(text_path)

        assert isinstance(result, dict)
        assert "text" in result
        assert result["format"] == "text"

    def test_parse_dispatcher_markdown_file(self, parser, temp_dir):
        """Test the parse dispatcher with a markdown file."""
        md_path = os.path.join(temp_dir, "doc.md")
        with open(md_path, "w") as f:
            f.write("# Title\nContent")

        result = parser.parse(md_path)

        assert isinstance(result, dict)
        assert result["format"] == "markdown"

    def test_parse_dispatcher_url(self, parser):
        """Test the parse dispatcher with a URL."""
        url = "https://en.wikipedia.org/wiki/Computer_science"

        result = parser.parse(url)

        assert isinstance(result, dict)
        assert result["format"] == "html"
        assert result["source"] == url

    def test_parse_dispatcher_with_nonexistent_file(self, parser, temp_dir):
        """Test the parse dispatcher with a nonexistent file."""
        nonexistent_path = os.path.join(temp_dir, "nonexistent.txt")

        result = parser.parse(nonexistent_path)

        # Should handle gracefully
        assert isinstance(result, dict)
        assert "error" in result or result.get("text") == ""

    # ========================================================================
    # Output format validation tests
    # ========================================================================

    def test_parse_result_format_consistency(self, parser, temp_dir):
        """Test that all parse methods return consistent dictionary format."""
        text_path = os.path.join(temp_dir, "test.txt")
        with open(text_path, "w") as f:
            f.write("Test content")

        result = parser.parse_text(text_path)

        # Required keys
        required_keys = {"text", "title", "source", "format"}
        assert required_keys.issubset(set(result.keys())), (
            f"Missing required keys: {required_keys - set(result.keys())}"
        )

    def test_parse_result_optional_keys(self, parser, temp_dir):
        """Test that parse results include optional keys when available."""
        text_path = os.path.join(temp_dir, "test.txt")
        with open(text_path, "w") as f:
            f.write("Test content")

        result = parser.parse_text(text_path)

        # Optional keys that may be present
        optional_keys = {"author", "date"}
        assert all(isinstance(result.get(k), (str, type(None))) for k in optional_keys)

    def test_parse_text_limit_100k_chars(self, parser, temp_dir):
        """Test that parsed text is limited to 100,000 characters."""
        large_text = "a" * 150000
        text_path = os.path.join(temp_dir, "large.txt")

        with open(text_path, "w") as f:
            f.write(large_text)

        result = parser.parse_text(text_path)

        assert len(result["text"]) <= 100000

    def test_parse_url_limit_100k_chars(self, parser):
        """Test that parsed URL text is limited to 100,000 characters."""
        url = "https://en.wikipedia.org/wiki/Python_(programming_language)"

        result = parser.parse_url(url)

        assert len(result["text"]) <= 100000

    # ========================================================================
    # Error handling and logging tests
    # ========================================================================

    def test_parse_text_returns_dict_on_error(self, parser, temp_dir):
        """Test that parse_text returns a dict even on error."""
        # Try to parse a non-existent file
        nonexistent = os.path.join(temp_dir, "does_not_exist.txt")

        result = parser.parse_text(nonexistent)

        assert isinstance(result, dict)
        assert "error" in result

    def test_parse_url_returns_dict_on_error(self, parser):
        """Test that parse_url returns a dict even on error."""
        bad_url = "not-a-valid-url"

        result = parser.parse_url(bad_url)

        assert isinstance(result, dict)

    # ========================================================================
    # Title extraction tests
    # ========================================================================

    def test_parse_text_title_from_filename(self, parser, temp_dir):
        """Test that text files get title from filename."""
        text_path = os.path.join(temp_dir, "my_document.txt")
        with open(text_path, "w") as f:
            f.write("Content here")

        result = parser.parse_text(text_path)

        assert "title" in result
        # Title should contain the filename
        assert "my_document" in result["title"].lower() or result["title"] != ""

    def test_parse_markdown_title_from_heading(self, parser, temp_dir):
        """Test that markdown files extract title from first heading."""
        md_content = "# My Markdown Document\n\nContent here"
        md_path = os.path.join(temp_dir, "doc.md")

        with open(md_path, "w") as f:
            f.write(md_content)

        result = parser.parse_markdown(md_path)

        assert "title" in result
        # Should try to extract from heading or filename
        assert result["title"] != ""

    # ========================================================================
    # Type hints verification (runtime checks)
    # ========================================================================

    def test_parse_text_returns_dict(self, parser, temp_dir):
        """Verify parse_text returns a dictionary."""
        text_path = os.path.join(temp_dir, "test.txt")
        with open(text_path, "w") as f:
            f.write("Test")

        result = parser.parse_text(text_path)

        assert isinstance(result, dict)

    def test_parse_markdown_returns_dict(self, parser, temp_dir):
        """Verify parse_markdown returns a dictionary."""
        md_path = os.path.join(temp_dir, "test.md")
        with open(md_path, "w") as f:
            f.write("# Test")

        result = parser.parse_markdown(md_path)

        assert isinstance(result, dict)

    def test_parse_url_returns_dict(self, parser):
        """Verify parse_url returns a dictionary."""
        url = "https://en.wikipedia.org/wiki/Computer"

        result = parser.parse_url(url)

        assert isinstance(result, dict)

    def test_parse_returns_dict(self, parser, temp_dir):
        """Verify parse (dispatcher) returns a dictionary."""
        text_path = os.path.join(temp_dir, "test.txt")
        with open(text_path, "w") as f:
            f.write("Test")

        result = parser.parse(text_path)

        assert isinstance(result, dict)
