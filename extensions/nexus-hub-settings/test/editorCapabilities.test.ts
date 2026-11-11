import { expect, it } from "vitest";
import { editorCapabilities } from "../src/editorCapabilities";

it.each([
  ["Visual Studio Code", true, true, true],
  ["Visual Studio Code", false, true, false],
  ["Cursor", false, false, true],
  ["Antigravity", false, false, false],
  ["Antigravity", true, false, false],
])("exposes supported settings in %s with provider %s", (editor, provider, extensionSettings, fastMode) => {
  expect(editorCapabilities(editor, provider)).toEqual({extensionSettings, fastMode});
});
