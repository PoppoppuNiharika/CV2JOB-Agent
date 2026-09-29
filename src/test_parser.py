from __future__ import annotations

import sys
import tempfile
from io import BytesIO
from pathlib import Path

import pytest
from docx import Document

from parser import (
    CVParser,
    DocumentParseError,
)


# =========================================================
# FILE PATHS
# =========================================================

BASE_DIR = (
    Path(__file__).resolve().parent.parent
)


# =========================================================
# PYTEST FIXTURES
# =========================================================

@pytest.fixture
def parser() -> CVParser:
    """
    Provide a fresh CVParser instance to each pytest test.
    """

    return CVParser()


# =========================================================
# EXISTING PDF TEST
# =========================================================

def test_existing_pdf(
    parser: CVParser,
) -> None:

    pdf_path = (
        BASE_DIR / "test_cv.pdf"
    )

    if not pdf_path.exists():

        pytest.skip(
            "test_cv.pdf was not found."
        )

    text = parser.parse(
        pdf_path
    )

    assert text.strip(), (
        "PDF parser returned empty text."
    )

    links = parser.extract_links(
        pdf_path
    )

    assert isinstance(
        links,
        list,
    )

    for link in links:

        assert isinstance(
            link,
            str,
        )

        assert link.strip()

    print(
        f"PDF text characters: {len(text)}"
    )

    print(
        f"PDF links found: {len(links)}"
    )


# =========================================================
# EXISTING TXT TEST
# =========================================================

def test_existing_txt(
    parser: CVParser,
) -> None:

    txt_path = (
        BASE_DIR
        / "test_job_description.txt"
    )

    if not txt_path.exists():

        pytest.skip(
            "test_job_description.txt was not found."
        )

    text = parser.parse(
        txt_path
    )

    assert text.strip(), (
        "TXT parser returned empty text."
    )

    assert "Python" in text, (
        "Expected Python in test job description."
    )

    print(
        f"TXT text characters: {len(text)}"
    )


# =========================================================
# DOCX TEST
# =========================================================

def test_docx(
    parser: CVParser,
) -> None:

    with tempfile.TemporaryDirectory() as temp_dir:

        docx_path = (
            Path(temp_dir)
            / "sample.docx"
        )

        document = Document()

        document.add_paragraph(
            "Sample Candidate"
        )

        document.add_paragraph(
            "Technical Skills"
        )

        document.add_paragraph(
            "Python, SQL, Pandas"
        )

        table = document.add_table(
            rows=1,
            cols=2,
        )

        table.cell(
            0,
            0,
        ).text = (
            "Education"
        )

        table.cell(
            0,
            1,
        ).text = (
            "B.Tech Computer Science"
        )

        document.save(
            docx_path
        )

        text = parser.parse(
            docx_path
        )

        assert (
            "Sample Candidate" in text
        )

        assert (
            "Technical Skills" in text
        )

        assert (
            "Python, SQL, Pandas" in text
        )

        assert (
            "B.Tech Computer Science"
            in text
        )

        print(
            "DOCX parsing: PASS"
        )


# =========================================================
# BYTES INPUT TEST
# =========================================================

def test_bytes_input(
    parser: CVParser,
) -> None:

    data = (
        b"Python\n"
        b"SQL\n"
        b"Data Analysis\n"
    )

    text = parser.parse(
        data,
        file_name="sample.txt",
    )

    assert text.strip(), (
        "Bytes input returned empty text."
    )

    assert "Python" in text
    assert "SQL" in text
    assert "Data Analysis" in text

    print(
        "Bytes input: PASS"
    )


# =========================================================
# UNSUPPORTED FILE TEST
# =========================================================

def test_unsupported_file(
    parser: CVParser,
) -> None:

    with pytest.raises(
        (
            ValueError,
            DocumentParseError,
        )
    ):

        parser.parse(
            b"some content",
            file_name="sample.exe",
        )

    print(
        "Unsupported file handling: PASS"
    )


# =========================================================
# EMPTY TEXT VALIDATION
# =========================================================

def test_empty_text_is_rejected(
    parser: CVParser,
) -> None:

    with pytest.raises(
        (
            ValueError,
            DocumentParseError,
        )
    ):

        parser.parse(
            b"",
            file_name="empty.txt",
        )


# =========================================================
# FILE-LIKE INPUT TEST
# =========================================================

def test_file_like_input(
    parser: CVParser,
) -> None:

    data = BytesIO(
        b"Python\nSQL\nPandas\n"
    )

    text = parser.parse(
        data,
        file_name="sample.txt",
    )

    assert text.strip()

    assert "Python" in text
    assert "SQL" in text
    assert "Pandas" in text


# =========================================================
# LINK EXTRACTION TEST
# =========================================================

def test_pdf_links_are_strings(
    parser: CVParser,
) -> None:

    pdf_path = (
        BASE_DIR / "test_cv.pdf"
    )

    if not pdf_path.exists():

        pytest.skip(
            "test_cv.pdf was not found."
        )

    links = parser.extract_links(
        pdf_path
    )

    assert isinstance(
        links,
        list,
    )

    for link in links:

        assert isinstance(
            link,
            str,
        )

        assert link.strip()


# =========================================================
# PARSE WITH LINKS TEST
# =========================================================

def test_parse_with_links(
    parser: CVParser,
) -> None:

    pdf_path = (
        BASE_DIR / "test_cv.pdf"
    )

    if not pdf_path.exists():

        pytest.skip(
            "test_cv.pdf was not found."
        )

    result = parser.parse_with_links(
        pdf_path
    )

    # The current CVParser API returns:
    #
    #     (text, links)
    #
    # where:
    #     text  -> extracted document text
    #     links -> list of embedded URLs
    assert isinstance(
        result,
        tuple,
    )

    assert len(result) == 2

    text, links = result

    assert isinstance(
        text,
        str,
    )

    assert isinstance(
        links,
        list,
    )

    assert text.strip()

    for link in links:

        assert isinstance(
            link,
            str,
        )

        assert link.strip()

    # The test CV currently contains embedded links.
    assert len(links) >= 1


# =========================================================
# STANDALONE TEST
# =========================================================

def main() -> None:

    parser = CVParser()

    print("=" * 70)
    print("DOCUMENT PARSER TEST")
    print("=" * 70)

    try:

        test_existing_pdf(
            parser
        )

        test_existing_txt(
            parser
        )

        test_docx(
            parser
        )

        test_bytes_input(
            parser
        )

        test_unsupported_file(
            parser
        )

        print()
        print(
            "=" * 70
        )
        print(
            "DOCUMENT PARSER TEST: SUCCESS"
        )
        print(
            "=" * 70
        )

    except pytest.skip.Exception:

        raise

    except Exception as error:

        print()
        print(
            "=" * 70
        )
        print(
            "DOCUMENT PARSER TEST: FAILED"
        )
        print(
            "=" * 70
        )

        print(
            f"{type(error).__name__}: {error}"
        )

        sys.exit(1)


if __name__ == "__main__":

    main()