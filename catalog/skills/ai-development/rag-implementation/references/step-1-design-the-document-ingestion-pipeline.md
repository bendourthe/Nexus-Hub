### Step 1: Design the Document Ingestion Pipeline

Before building retrieval, you need clean, structured documents. The quality of ingested data determines the ceiling for retrieval quality.

**Document Loader Architecture**:

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Document:
    """A single document with content and metadata."""
    content: str
    metadata: dict = field(default_factory=dict)
    source: str = ""
    doc_type: str = ""


class DocumentLoader(ABC):
    """Base class for document loaders."""

    @abstractmethod
    def load(self, source: str) -> list[Document]:
        ...


class PDFLoader(DocumentLoader):
    """Load and extract text from PDF files."""

    def load(self, source: str) -> list[Document]:
        import pymupdf  # PyMuPDF

        docs = []
        pdf = pymupdf.open(source)
        for page_num, page in enumerate(pdf):
            text = page.get_text("text")
            if text.strip():
                docs.append(Document(
                    content=text,
                    metadata={
                        "page": page_num + 1,
                        "total_pages": len(pdf),
                    },
                    source=source,
                    doc_type="pdf",
                ))
        pdf.close()
        return docs


class HTMLLoader(DocumentLoader):
    """Load and extract text from HTML, stripping boilerplate."""

    def load(self, source: str) -> list[Document]:
        from bs4 import BeautifulSoup
        import requests

        if source.startswith("http"):
            html = requests.get(source, timeout=30).text
        else:
            html = Path(source).read_text(encoding="utf-8")

        soup = BeautifulSoup(html, "html.parser")

        # Remove navigation, headers, footers, scripts
        for tag in soup.find_all(["nav", "header", "footer", "script", "style"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)

        return [Document(
            content=text,
            metadata={"title": soup.title.string if soup.title else ""},
            source=source,
            doc_type="html",
        )]


class CodeLoader(DocumentLoader):
    """Load source code files with language-aware metadata."""

    LANGUAGE_MAP = {
        ".py": "python", ".js": "javascript", ".ts": "typescript",
        ".go": "go", ".rs": "rust", ".java": "java", ".cs": "csharp",
    }

    def load(self, source: str) -> list[Document]:
        path = Path(source)
        content = path.read_text(encoding="utf-8")
        language = self.LANGUAGE_MAP.get(path.suffix, "unknown")

        return [Document(
            content=content,
            metadata={
                "language": language,
                "filename": path.name,
                "extension": path.suffix,
                "line_count": content.count("\n") + 1,
            },
            source=source,
            doc_type="code",
        )]
```

**Unified Ingestion Pipeline**:

```python
class IngestionPipeline:
    """Orchestrate document loading, cleaning, and chunking."""

    def __init__(self):
        self.loaders: dict[str, DocumentLoader] = {
            ".pdf": PDFLoader(),
            ".html": HTMLLoader(),
            ".htm": HTMLLoader(),
            ".py": CodeLoader(),
            ".js": CodeLoader(),
            ".ts": CodeLoader(),
        }

    def ingest(self, sources: list[str]) -> list[Document]:
        """Load and clean documents from multiple sources."""
        documents = []
        for source in sources:
            ext = Path(source).suffix.lower() if not source.startswith("http") else ".html"
            loader = self.loaders.get(ext)
            if loader is None:
                print(f"Skipping unsupported format: {ext}")
                continue

            docs = loader.load(source)
            for doc in docs:
                doc.content = self._clean(doc.content)
            documents.extend(docs)

        return documents

    def _clean(self, text: str) -> str:
        """Normalize whitespace and remove artifacts."""
        import re
        text = re.sub(r"\n{3,}", "\n\n", text)     # Collapse excess newlines
        text = re.sub(r"[ \t]{2,}", " ", text)      # Collapse excess spaces
        text = text.strip()
        return text
```
