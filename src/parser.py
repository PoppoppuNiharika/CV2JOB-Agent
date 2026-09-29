from __future__ import annotations

import io
import re
from pathlib import Path
from typing import BinaryIO


try:
    import pymupdf
except ImportError as error:
    raise ImportError(
        "PyMuPDF is required. Install it with: "
        "python -m pip install pymupdf"
    ) from error


try:
    from docx import Document
    from docx.document import Document as DocumentType
    from docx.table import Table
    from docx.text.paragraph import Paragraph
    from docx.opc.constants import RELATIONSHIP_TYPE as RT
except ImportError as error:
    raise ImportError(
        "python-docx is required. Install it with: "
        "python -m pip install python-docx"
    ) from error


SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".txt",
}

DEFAULT_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


class DocumentParseError(ValueError):
    """Raised when a supported document cannot be parsed."""


class DocumentParser:
    """
    General-purpose document parser for CVs and job descriptions.

    Supported formats:
        - PDF
        - DOCX
        - TXT

    The parser accepts:
        - file paths
        - bytes
        - bytearray
        - file-like objects such as Streamlit UploadedFile
    """

    def __init__(
        self,
        max_file_size: int = DEFAULT_MAX_FILE_SIZE,
    ) -> None:

        if max_file_size <= 0:
            raise ValueError(
                "max_file_size must be greater than zero."
            )

        self.max_file_size = max_file_size

    # =========================================================
    # PUBLIC API
    # =========================================================

    def parse(
        self,
        source: str | Path | bytes | bytearray | BinaryIO,
        file_name: str | None = None,
    ) -> str:
        """
        Extract readable text from a supported document.

        Args:
            source:
                File path, bytes, bytearray, or file-like object.

            file_name:
                Optional filename when source is bytes or a file-like
                object without a usable 'name' attribute.

        Returns:
            Cleaned text.

        Raises:
            FileNotFoundError:
                If a supplied file path does not exist.

            ValueError:
                If the file type is unsupported or no readable text
                can be extracted.
        """

        data, extension = self._read_source(
            source,
            file_name=file_name,
        )

        if extension == ".pdf":
            text = self._parse_pdf(data)

        elif extension == ".docx":
            text = self._parse_docx(data)

        elif extension == ".txt":
            text = self._parse_txt(data)

        else:
            supported = ", ".join(
                sorted(SUPPORTED_EXTENSIONS)
            )

            raise DocumentParseError(
                f"Unsupported file type: {extension}. "
                f"Supported types: {supported}"
            )

        cleaned_text = self._clean_text(text)

        if not cleaned_text:
            raise DocumentParseError(
                "No readable text was extracted from the document. "
                "If this is a scanned PDF, OCR is required."
            )

        return cleaned_text

    def parse_with_links(
        self,
        source: str | Path | bytes | bytearray | BinaryIO,
        file_name: str | None = None,
    ) -> tuple[str, list[str]]:
        """
        Parse a document and return both text and embedded links.
        """

        text = self.parse(
            source,
            file_name=file_name,
        )

        links = self.extract_links(
            source,
            file_name=file_name,
        )

        return text, links

    def extract_links(
        self,
        source: str | Path | bytes | bytearray | BinaryIO,
        file_name: str | None = None,
    ) -> list[str]:
        """
        Extract hyperlinks from PDF and DOCX files.

        For TXT files, URL-like strings are extracted from the text.
        """

        data, extension = self._read_source(
            source,
            file_name=file_name,
        )

        links: list[str] = []

        if extension == ".pdf":
            links.extend(
                self._extract_pdf_links(data)
            )

        elif extension == ".docx":
            links.extend(
                self._extract_docx_links(data)
            )

        elif extension == ".txt":
            text = self._parse_txt(data)

            links.extend(
                self._extract_urls_from_text(text)
            )

        return self._deduplicate_links(links)

    # =========================================================
    # SOURCE HANDLING
    # =========================================================

    def _read_source(
        self,
        source: str | Path | bytes | bytearray | BinaryIO,
        file_name: str | None = None,
    ) -> tuple[bytes, str]:

        # -----------------------------------------------------
        # Path
        # -----------------------------------------------------

        if isinstance(source, (str, Path)):

            path = Path(source)

            if not path.exists():
                raise FileNotFoundError(
                    f"File not found: {path}"
                )

            if not path.is_file():
                raise DocumentParseError(
                    f"Source is not a file: {path}"
                )

            extension = path.suffix.lower()

            data = path.read_bytes()

            self._validate_file_size(
                data,
                path.name,
            )

            return data, extension

        # -----------------------------------------------------
        # Raw bytes
        # -----------------------------------------------------

        if isinstance(source, bytes):

            extension = self._get_extension(
                file_name
            )

            self._validate_file_size(
                source,
                file_name or "uploaded file",
            )

            return source, extension

        # -----------------------------------------------------
        # Bytearray
        # -----------------------------------------------------

        if isinstance(source, bytearray):

            data = bytes(source)

            extension = self._get_extension(
                file_name
            )

            self._validate_file_size(
                data,
                file_name or "uploaded file",
            )

            return data, extension

        # -----------------------------------------------------
        # File-like object
        # -----------------------------------------------------

        if hasattr(source, "read"):

            name = file_name

            if not name:
                name = getattr(
                    source,
                    "name",
                    None,
                )

            extension = self._get_extension(name)

            data = self._read_file_like(
                source
            )

            self._validate_file_size(
                data,
                name or "uploaded file",
            )

            return data, extension

        raise TypeError(
            "source must be a file path, bytes, bytearray, "
            "or file-like object."
        )

    @staticmethod
    def _read_file_like(
        source: BinaryIO,
    ) -> bytes:

        # Streamlit UploadedFile exposes getvalue().
        if hasattr(source, "getvalue"):

            data = source.getvalue()

            if isinstance(data, bytes):
                return data

            return bytes(data)

        # Generic file-like object.
        current_position = None

        try:
            current_position = source.tell()
        except Exception:
            current_position = None

        try:
            source.seek(0)
        except Exception:
            pass

        data = source.read()

        if current_position is not None:

            try:
                source.seek(current_position)
            except Exception:
                pass

        if isinstance(data, bytes):
            return data

        if isinstance(data, bytearray):
            return bytes(data)

        raise TypeError(
            "File-like object must return bytes."
        )

    @staticmethod
    def _get_extension(
        file_name: str | None,
    ) -> str:

        if not file_name:
            raise ValueError(
                "file_name is required when parsing "
                "bytes or an unnamed file-like object."
            )

        extension = Path(
            file_name
        ).suffix.lower()

        if extension not in SUPPORTED_EXTENSIONS:

            supported = ", ".join(
                sorted(SUPPORTED_EXTENSIONS)
            )

            raise DocumentParseError(
                f"Unsupported file type: {extension or '[none]'}. "
                f"Supported types: {supported}"
            )

        return extension

    def _validate_file_size(
        self,
        data: bytes,
        name: str,
    ) -> None:

        if len(data) > self.max_file_size:

            size_mb = (
                len(data) / (1024 * 1024)
            )

            limit_mb = (
                self.max_file_size
                / (1024 * 1024)
            )

            raise DocumentParseError(
                f"File '{name}' is too large "
                f"({size_mb:.2f} MB). "
                f"Maximum allowed size is "
                f"{limit_mb:.2f} MB."
            )

        if not data:
            raise DocumentParseError(
                f"File '{name}' is empty."
            )

    # =========================================================
    # PDF
    # =========================================================

    def _parse_pdf(
        self,
        data: bytes,
    ) -> str:

        page_text: list[str] = []

        try:

            with pymupdf.open(
                stream=data,
                filetype="pdf",
            ) as document:

                for page in document:

                    text = page.get_text(
                        "text"
                    )

                    if text:
                        page_text.append(text)

        except Exception as error:

            raise DocumentParseError(
                f"Unable to read PDF document: {error}"
            ) from error

        return "\n".join(page_text)

    def _extract_pdf_links(
        self,
        data: bytes,
    ) -> list[str]:

        links: list[str] = []

        try:

            with pymupdf.open(
                stream=data,
                filetype="pdf",
            ) as document:

                for page in document:

                    for link in page.get_links():

                        uri = link.get("uri")

                        if uri:

                            uri = uri.strip()

                            if uri:
                                links.append(uri)

        except Exception as error:

            raise DocumentParseError(
                f"Unable to read PDF links: {error}"
            ) from error

        return links

    # =========================================================
    # DOCX
    # =========================================================

    def _parse_docx(
        self,
        data: bytes,
    ) -> str:

        try:

            document = Document(
                io.BytesIO(data)
            )

            content: list[str] = []

            # Preserve the order of paragraphs and tables.
            for child in document.element.body.iterchildren():

                tag = child.tag.lower()

                if tag.endswith("}p"):

                    paragraph = Paragraph(
                        child,
                        document,
                    )

                    text = paragraph.text.strip()

                    if text:
                        content.append(text)

                elif tag.endswith("}tbl"):

                    table = Table(
                        child,
                        document,
                    )

                    for row in table.rows:

                        cells: list[str] = []

                        for cell in row.cells:

                            cell_text = (
                                " ".join(
                                    cell.text.split()
                                ).strip()
                            )

                            if cell_text:
                                cells.append(
                                    cell_text
                                )

                        if cells:
                            content.append(
                                " | ".join(cells)
                            )

            return "\n".join(content)

        except Exception as error:

            raise DocumentParseError(
                f"Unable to read DOCX document: {error}"
            ) from error

    def _extract_docx_links(
        self,
        data: bytes,
    ) -> list[str]:

        links: list[str] = []

        try:

            document = Document(
                io.BytesIO(data)
            )

            for relationship in (
                document.part.rels.values()
            ):

                if relationship.reltype == RT.HYPERLINK:

                    target = (
                        relationship.target_ref
                    )

                    if target:
                        links.append(
                            target.strip()
                        )

        except Exception as error:

            raise DocumentParseError(
                f"Unable to read DOCX links: {error}"
            ) from error

        return links

    # =========================================================
    # TXT
    # =========================================================

    @staticmethod
    def _parse_txt(
        data: bytes,
    ) -> str:

        encodings = [
            "utf-8",
            "utf-8-sig",
            "cp1252",
            "latin-1",
        ]

        for encoding in encodings:

            try:

                return data.decode(
                    encoding
                )

            except UnicodeDecodeError:
                continue

        raise DocumentParseError(
            "Unable to decode the text file."
        )

    # =========================================================
    # URL EXTRACTION
    # =========================================================

    @staticmethod
    def _extract_urls_from_text(
        text: str,
    ) -> list[str]:

        pattern = (
            r"https?://[^\s<>\"]+"
        )

        return re.findall(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

    @staticmethod
    def _deduplicate_links(
        links: list[str],
    ) -> list[str]:

        result: list[str] = []
        seen: set[str] = set()

        for link in links:

            cleaned = link.strip()

            if not cleaned:
                continue

            key = cleaned.lower()

            if key not in seen:

                seen.add(key)
                result.append(cleaned)

        return result

    # =========================================================
    # TEXT CLEANING
    # =========================================================

    @staticmethod
    def _clean_text(
        text: str,
    ) -> str:

        lines: list[str] = []

        for line in text.splitlines():

            cleaned_line = " ".join(
                line.split()
            ).strip()

            if cleaned_line:
                lines.append(
                    cleaned_line
                )

        return "\n".join(lines)


class CVParser(DocumentParser):
    """
    Backward-compatible CV parser.

    Existing code can continue using:

        CVParser().parse(path)

    while the underlying implementation now supports
    PDF, DOCX, TXT, bytes, and uploaded-file objects.
    """

    pass


if __name__ == "__main__":

    print(
        "DocumentParser / CVParser is ready."
    )