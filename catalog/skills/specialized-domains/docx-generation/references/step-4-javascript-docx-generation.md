### Step 4: JavaScript DOCX Generation

The `docx` npm package provides a TypeScript-first declarative API for building Word documents in Node.js. It uses a builder pattern where you compose document elements as nested objects.

**Core Document Structure**:

```typescript
import {
  Document,
  Packer,
  Paragraph,
  TextRun,
  HeadingLevel,
  AlignmentType,
  Table,
  TableRow,
  TableCell,
  WidthType,
  BorderStyle,
  Header,
  Footer,
  PageNumber,
  NumberFormat,
  ImageRun,
  ShadingType,
  convertInchesToTwip,
  Tab,
  TabStopPosition,
  TabStopType,
} from "docx";
import * as fs from "fs";
import * as path from "path";

interface ReportSection {
  heading: string;
  level: (typeof HeadingLevel)[keyof typeof HeadingLevel];
  paragraphs: string[];
}

function createReport(
  title: string,
  author: string,
  sections: ReportSection[],
): Document {
  const children: Paragraph[] = [];

  // Title
  children.push(
    new Paragraph({
      text: title,
      heading: HeadingLevel.TITLE,
      alignment: AlignmentType.CENTER,
      spacing: { after: 200 },
    }),
  );

  // Author line
  children.push(
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 400 },
      children: [
        new TextRun({
          text: `Prepared by: ${author}`,
          size: 24, // half-points: 24 = 12pt
          color: "666666",
          font: "Calibri",
        }),
      ],
    }),
  );

  // Sections
  for (const section of sections) {
    children.push(
      new Paragraph({
        text: section.heading,
        heading: section.level,
        spacing: { before: 240, after: 120 },
      }),
    );
    for (const text of section.paragraphs) {
      children.push(
        new Paragraph({
          children: [
            new TextRun({
              text,
              size: 22, // 11pt
              font: "Calibri",
            }),
          ],
          spacing: { after: 120 },
        }),
      );
    }
  }

  return new Document({
    creator: author,
    title,
    sections: [
      {
        properties: {
          page: {
            margin: {
              top: convertInchesToTwip(1),
              bottom: convertInchesToTwip(1),
              left: convertInchesToTwip(1.25),
              right: convertInchesToTwip(1.25),
            },
          },
        },
        headers: {
          default: new Header({
            children: [
              new Paragraph({
                alignment: AlignmentType.RIGHT,
                children: [
                  new TextRun({
                    text: title,
                    italics: true,
                    size: 18,
                    color: "999999",
                  }),
                ],
              }),
            ],
          }),
        },
        footers: {
          default: new Footer({
            children: [
              new Paragraph({
                alignment: AlignmentType.CENTER,
                children: [
                  new TextRun({ text: "Page ", size: 18 }),
                  new TextRun({
                    children: [PageNumber.CURRENT],
                    size: 18,
                  }),
                  new TextRun({ text: " of ", size: 18 }),
                  new TextRun({
                    children: [PageNumber.TOTAL_PAGES],
                    size: 18,
                  }),
                ],
              }),
            ],
          }),
        },
        children,
      },
    ],
  });
}

// Save to file
async function saveDocument(doc: Document, filePath: string): Promise<void> {
  const buffer = await Packer.toBuffer(doc);
  fs.writeFileSync(filePath, buffer);
}
```

**Tables in the docx npm Package**:

```typescript
import {
  Table,
  TableRow,
  TableCell,
  Paragraph,
  TextRun,
  WidthType,
  AlignmentType,
  ShadingType,
  BorderStyle,
  convertInchesToTwip,
} from "docx";

interface TableData {
  headers: string[];
  rows: string[][];
}

function createStyledTable(data: TableData): Table {
  const headerCells = data.headers.map(
    (text) =>
      new TableCell({
        children: [
          new Paragraph({
            alignment: AlignmentType.CENTER,
            children: [
              new TextRun({
                text,
                bold: true,
                color: "FFFFFF",
                size: 20,
                font: "Calibri",
              }),
            ],
          }),
        ],
        shading: { fill: "2B579A", type: ShadingType.CLEAR },
        width: { size: 100 / data.headers.length, type: WidthType.PERCENTAGE },
      }),
  );

  const dataRows = data.rows.map(
    (row, rowIdx) =>
      new TableRow({
        children: row.map(
          (cellText) =>
            new TableCell({
              children: [
                new Paragraph({
                  children: [
                    new TextRun({
                      text: cellText,
                      size: 18,
                      font: "Calibri",
                    }),
                  ],
                }),
              ],
              shading:
                rowIdx % 2 === 1
                  ? { fill: "F2F2F2", type: ShadingType.CLEAR }
                  : undefined,
            }),
        ),
      }),
  );

  return new Table({
    rows: [new TableRow({ children: headerCells }), ...dataRows],
    width: { size: 100, type: WidthType.PERCENTAGE },
  });
}
```

**Generating DOCX in Serverless / Express Endpoints**:

```typescript
import express from "express";
import { Document, Packer, Paragraph, HeadingLevel } from "docx";

const app = express();
app.use(express.json());

app.post("/api/generate-report", async (req, res) => {
  const { title, sections } = req.body;

  const doc = new Document({
    sections: [
      {
        children: [
          new Paragraph({ text: title, heading: HeadingLevel.HEADING_1 }),
          ...sections.map(
            (s: { text: string }) => new Paragraph({ text: s.text }),
          ),
        ],
      },
    ],
  });

  const buffer = await Packer.toBuffer(doc);

  res.setHeader(
    "Content-Type",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  );
  res.setHeader("Content-Disposition", `attachment; filename="${title}.docx"`);
  res.send(Buffer.from(buffer));
});
```

**Critical Rules for JavaScript DOCX Generation**:

- Sizes in the docx npm package are in half-points (not points). A 12pt font is `size: 24`
- Use `convertInchesToTwip()` for margins and dimensions. One inch is 1440 twips
- The `Packer.toBuffer()` method is async. Always `await` it
- Table cells must contain at least one `Paragraph`. Empty cells cause invalid documents
- Images require the file bytes passed as a `Buffer` to `ImageRun`, not a file path
