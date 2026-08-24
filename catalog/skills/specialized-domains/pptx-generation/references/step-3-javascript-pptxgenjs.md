### Step 3: JavaScript PptxGenJS

PptxGenJS is a zero-dependency JavaScript library that generates PPTX files in both browser and Node.js environments. It provides a fluent API for creating slides with text, images, charts, tables, and shapes.

**Creating a Presentation (Node.js)**:

```typescript
import PptxGenJS from "pptxgenjs";

interface SlideTheme {
  primaryColor: string;
  secondaryColor: string;
  fontFamily: string;
  titleSize: number;
  bodySize: number;
}

const DEFAULT_THEME: SlideTheme = {
  primaryColor: "2E4A7A",
  secondaryColor: "5B8DEF",
  fontFamily: "Segoe UI",
  titleSize: 28,
  bodySize: 14,
};

function createPresentation(theme: SlideTheme = DEFAULT_THEME): PptxGenJS {
  const pptx = new PptxGenJS();

  // Set presentation metadata
  pptx.author = "Automated Report Generator";
  pptx.company = "Your Company";
  pptx.subject = "Generated Presentation";

  // Set 16:9 layout
  pptx.layout = "LAYOUT_16x9";

  // Define reusable master slides
  pptx.defineSlideMaster({
    title: "TITLE_SLIDE",
    background: { color: theme.primaryColor },
    objects: [
      {
        placeholder: {
          options: {
            name: "title",
            type: "title",
            x: 1.0,
            y: 2.5,
            w: 11.0,
            h: 1.5,
            fontFace: theme.fontFamily,
            fontSize: 36,
            color: "FFFFFF",
            align: "center",
          },
          text: "",
        },
      },
      {
        placeholder: {
          options: {
            name: "subtitle",
            type: "body",
            x: 2.0,
            y: 4.2,
            w: 9.0,
            h: 1.0,
            fontFace: theme.fontFamily,
            fontSize: 18,
            color: "CCCCCC",
            align: "center",
          },
          text: "",
        },
      },
    ],
  });

  pptx.defineSlideMaster({
    title: "CONTENT_SLIDE",
    background: { color: "FFFFFF" },
    objects: [
      {
        rect: {
          x: 0,
          y: 0,
          w: "100%",
          h: 0.75,
          fill: { color: theme.primaryColor },
        },
      },
      {
        placeholder: {
          options: {
            name: "title",
            type: "title",
            x: 0.5,
            y: 0.1,
            w: 12.0,
            h: 0.55,
            fontFace: theme.fontFamily,
            fontSize: 22,
            color: "FFFFFF",
            bold: true,
          },
          text: "",
        },
      },
    ],
  });

  return pptx;
}
```

**Adding Slides with Content**:

```typescript
function addTitleSlide(
  pptx: PptxGenJS,
  title: string,
  subtitle: string,
): void {
  const slide = pptx.addSlide({ masterName: "TITLE_SLIDE" });
  slide.addText(title, {
    placeholder: "title",
  });
  slide.addText(subtitle, {
    placeholder: "subtitle",
  });
}

function addContentSlide(
  pptx: PptxGenJS,
  title: string,
  bulletPoints: string[],
  theme: SlideTheme = DEFAULT_THEME,
): void {
  const slide = pptx.addSlide({ masterName: "CONTENT_SLIDE" });
  slide.addText(title, { placeholder: "title" });

  const textRows = bulletPoints.map((point) => ({
    text: point,
    options: {
      fontSize: theme.bodySize,
      fontFace: theme.fontFamily,
      color: "333333",
      bullet: { type: "bullet" as const },
      paraSpaceAfter: 6,
    },
  }));

  slide.addText(textRows, {
    x: 0.75,
    y: 1.2,
    w: 11.5,
    h: 5.5,
    valign: "top",
  });
}
```

**Adding Tables**:

```typescript
interface TableConfig {
  headers: string[];
  rows: string[][];
  theme?: SlideTheme;
}

function addTableSlide(
  pptx: PptxGenJS,
  title: string,
  config: TableConfig,
): void {
  const theme = config.theme ?? DEFAULT_THEME;
  const slide = pptx.addSlide({ masterName: "CONTENT_SLIDE" });
  slide.addText(title, { placeholder: "title" });

  const headerRow: PptxGenJS.TableCell[] = config.headers.map((h) => ({
    text: h,
    options: {
      bold: true,
      color: "FFFFFF",
      fill: { color: theme.primaryColor },
      fontSize: 11,
      align: "center" as const,
    },
  }));

  const dataRows: PptxGenJS.TableCell[][] = config.rows.map((row) =>
    row.map((cell) => ({
      text: cell,
      options: {
        fontSize: 10,
        color: "333333",
        border: { type: "solid", pt: 0.5, color: "CCCCCC" },
      },
    })),
  );

  slide.addTable([headerRow, ...dataRows], {
    x: 0.5,
    y: 1.2,
    w: 12.0,
    colW: config.headers.map(() => 12.0 / config.headers.length),
    rowH: 0.4,
    autoPage: true,
    autoPageRepeatHeader: true,
  });
}
```

**Adding Images and Shapes**:

```typescript
import * as fs from "node:fs";
import * as path from "node:path";

function addImageSlide(
  pptx: PptxGenJS,
  title: string,
  imagePath: string,
): void {
  const slide = pptx.addSlide({ masterName: "CONTENT_SLIDE" });
  slide.addText(title, { placeholder: "title" });

  // Read image as base64 for Node.js
  const imageBuffer = fs.readFileSync(imagePath);
  const base64 = imageBuffer.toString("base64");
  const ext = path.extname(imagePath).slice(1).toLowerCase();

  slide.addImage({
    data: `image/${ext};base64,${base64}`,
    x: 2.0,
    y: 1.5,
    w: 9.0,
    h: 5.0,
    sizing: { type: "contain", w: 9.0, h: 5.0 },
  });
}

function addShapeSlide(pptx: PptxGenJS, title: string): void {
  const slide = pptx.addSlide({ masterName: "CONTENT_SLIDE" });
  slide.addText(title, { placeholder: "title" });

  // Add a rounded rectangle with text
  slide.addShape(pptx.ShapeType.roundRect, {
    x: 3.0,
    y: 2.0,
    w: 7.0,
    h: 3.0,
    fill: { color: "E8F0FE" },
    line: { color: "2E4A7A", width: 2 },
    rectRadius: 0.2,
  });

  slide.addText("Key Insight", {
    x: 3.5,
    y: 3.0,
    w: 6.0,
    h: 1.0,
    fontSize: 24,
    color: "2E4A7A",
    align: "center",
    bold: true,
  });
}
```

**Saving (Node.js and Browser)**:

```typescript
// Node.js: save to file
async function saveToFile(
  pptx: PptxGenJS,
  outputPath: string,
): Promise<string> {
  await pptx.writeFile({ fileName: outputPath });
  return outputPath;
}

// Browser: trigger download
async function downloadInBrowser(
  pptx: PptxGenJS,
  fileName: string,
): Promise<void> {
  await pptx.writeFile({ fileName });
  // PptxGenJS handles the browser download automatically
}

// Get as base64 (for API responses)
async function toBase64(pptx: PptxGenJS): Promise<string> {
  const output = await pptx.write({ outputType: "base64" });
  return output as string;
}
```
