export interface EditorCapabilities {
  extensionSettings: boolean;
  fastMode: boolean;
}

/** Only expose controls backed by this editor's integrations. */
export function editorCapabilities(appName: string, hasFastProvider: boolean): EditorCapabilities {
  if (/antigravity|gemini/i.test(appName)) { return {extensionSettings: false, fastMode: false}; }
  if (/cursor/i.test(appName)) { return {extensionSettings: false, fastMode: true}; }
  return {extensionSettings: true, fastMode: hasFastProvider};
}
