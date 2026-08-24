### Step 7: Mail Merge and Batch Generation

Data-driven document generation produces personalized documents at scale. Common use cases include contracts, certificates, letters, invoices, and compliance reports.

**Batch Document Generator**:

```python
from docxtpl import DocxTemplate
from pathlib import Path
from dataclasses import dataclass
from concurrent.futures import ProcessPoolExecutor, as_completed
import json
import csv
import logging

logger = logging.getLogger(__name__)

@dataclass
class BatchResult:
    total: int
    succeeded: int
    failed: int
    errors: list[dict]
    output_paths: list[Path]

def generate_batch_documents(
    template_path: str | Path,
    data_source: str | Path,
    output_dir: str | Path,
    filename_pattern: str = "{index:04d}_{name}",
    max_workers: int = 4,
) -> BatchResult:
    """Generate multiple documents from a template and data source.

    Args:
        template_path: Path to the .docx template.
        data_source: Path to a JSON or CSV file containing row data.
        output_dir: Directory where generated documents are saved.
        filename_pattern: Pattern for output filenames. Supports {index}, {name},
            and any key from the data row.
        max_workers: Number of parallel workers for generation.

    Returns:
        BatchResult with counts and paths of generated documents.
    """
    template_path = Path(template_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    data_path = Path(data_source)
    if data_path.suffix == ".json":
        with open(data_path) as f:
            records = json.load(f)
    elif data_path.suffix == ".csv":
        with open(data_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            records = list(reader)
    else:
        raise ValueError(f"Unsupported data format: {data_path.suffix}. Use .json or .csv")

    results = BatchResult(total=len(records), succeeded=0, failed=0, errors=[], output_paths=[])

    for index, record in enumerate(records):
        try:
            # Each iteration loads a fresh template to avoid state leakage
            tpl = DocxTemplate(str(template_path))

            context = {**record, "index": index}

            # Generate filename
            safe_name = record.get("name", f"doc_{index}").replace(" ", "_").replace("/", "_")
            filename = filename_pattern.format(index=index, name=safe_name, **record)
            output_path = output_dir / f"{filename}.docx"

            tpl.render(context)
            tpl.save(str(output_path))

            results.output_paths.append(output_path)
            results.succeeded += 1
            logger.info("Generated document %d/%d: %s", index + 1, results.total, output_path.name)

        except Exception as exc:
            results.failed += 1
            results.errors.append({
                "index": index,
                "record": record,
                "error": str(exc),
            })
            logger.error("Failed to generate document %d: %s", index, exc)

    return results


# Usage
result = generate_batch_documents(
    template_path="templates/certificate.docx",
    data_source="data/graduates.csv",
    output_dir="output/certificates",
    filename_pattern="{index:04d}_{name}",
)
print(f"Generated {result.succeeded}/{result.total} documents, {result.failed} failures")
```

**Conditional Sections in Templates**:

```
{# In the Word template, use paragraph-level conditionals for optional sections #}

{%p if contract_type == "enterprise" %}
ENTERPRISE SERVICE LEVEL AGREEMENT

This Enterprise SLA provides guaranteed 99.99% uptime with dedicated support
and a named account manager assigned to {{ client_name }}.
{%p endif %}

{%p if contract_type == "standard" %}
STANDARD SERVICE LEVEL AGREEMENT

This Standard SLA provides 99.9% uptime with business-hours support.
{%p endif %}

{%p if include_data_processing_addendum %}
DATA PROCESSING ADDENDUM

This addendum governs the processing of personal data under the agreement
between {{ company_name }} and {{ client_name }}, effective {{ effective_date }}.
{%p endif %}
```

**Mail Merge from Database**:

```python
from docxtpl import DocxTemplate
from pathlib import Path
import asyncio
import asyncpg

async def mail_merge_from_database(
    template_path: str | Path,
    output_dir: str | Path,
    db_url: str,
    query: str,
    filename_column: str = "id",
) -> list[Path]:
    """Generate documents by querying a database for merge data.

    Args:
        template_path: Path to the .docx template.
        output_dir: Directory for generated documents.
        db_url: PostgreSQL connection string.
        query: SQL query that returns one row per document.
        filename_column: Column used to name each output file.

    Returns:
        List of paths to generated documents.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []

    conn = await asyncpg.connect(db_url)
    try:
        rows = await conn.fetch(query)
        for row in rows:
            context = dict(row)
            tpl = DocxTemplate(str(template_path))
            tpl.render(context)

            filename = f"{context[filename_column]}.docx"
            output_path = output_dir / filename
            tpl.save(str(output_path))
            generated.append(output_path)
    finally:
        await conn.close()

    return generated


# Usage
# asyncio.run(mail_merge_from_database(
#     template_path="templates/invoice.docx",
#     output_dir="output/invoices",
#     db_url="postgresql://user:pass@localhost/billing",
#     query="SELECT * FROM invoices WHERE status = 'pending' AND issue_date = CURRENT_DATE",
#     filename_column="invoice_number",
# ))
```

**Merging Multiple DOCX Files**:

```python
from docx import Document
from docxcompose.composer import Composer
from pathlib import Path

def merge_documents(
    source_paths: list[str | Path],
    output_path: str | Path,
    add_page_breaks: bool = True,
) -> Path:
    """Merge multiple DOCX files into a single document.

    Requires the docxcompose package: pip install docxcompose

    Args:
        source_paths: Ordered list of .docx files to merge.
        output_path: Path for the combined document.
        add_page_breaks: Whether to insert a page break between documents.

    Returns:
        Path to the merged document.
    """
    if not source_paths:
        raise ValueError("At least one source document is required")

    base_doc = Document(str(source_paths[0]))
    composer = Composer(base_doc)

    for doc_path in source_paths[1:]:
        if add_page_breaks:
            composer.doc.add_page_break()
        sub_doc = Document(str(doc_path))
        composer.append(sub_doc)

    output = Path(output_path)
    composer.save(str(output))
    return output
```

**Critical Rules for Batch Generation**:

- Always load a fresh `DocxTemplate` instance for each document. Reusing a template after `render()` carries over state from the previous render
- Sanitize filenames derived from data fields. Remove or replace characters that are invalid in file paths (`/`, `\`, `:`, `*`, `?`, `"`, `<`, `>`, `|`)
- For large batches (1000+ documents), generate sequentially rather than loading all templates into memory at once. Each `DocxTemplate` instance holds the full document in memory
- Validate your data source before starting the batch. A missing required field in row 500 wastes the time spent on rows 1-499 if the process aborts
- Log progress and errors to a file so that failed documents can be retried without re-generating successful ones
