import * as vscode from "vscode";
import { UrgencyLevel } from "./types";
import { formatResetLabel } from "./usageStore";
import { UsageSuggestion } from "./recommendations";

/**
 * The usage-threshold warning as a WebviewView hosted in a narrow activity-bar
 * container, rather than a full-width editor tab. A WebviewView lives in a
 * contributed view container and fills only the (user-resizable) sidebar width,
 * which keeps the warning from stealing a whole editor column.
 *
 * Visibility is gated by the `geminiUsage.warningActive` context key: the view
 * (and its container icon) exist only while a warning is live, so revealing it
 * on a threshold crossing and dismissing it via Cancel both map cleanly onto
 * flipping that context key. Icons render as a stacked, narrow card. VS Code
 * notifications render `$(...)` literally and collapse newlines, so the icon-rich
 * layout is only achievable in a webview.
 */
export const WARNING_VIEW_ID = "geminiUsageWarningView";
export const WARNING_ACTIVE_CONTEXT = "geminiUsage.warningActive";

export interface WarningCallbacks {
  onOpenDashboard: () => void;
}

const URGENCY_COLOR: Record<UrgencyLevel, string> = {
  low: "#3fb950",
  moderate: "#d29922",
  high: "#db6d28",
  critical: "#f85149",
};

// The full-color Antigravity logo (icons/google-antigravity.svg), inlined so the
// strict webview CSP (img-src data:) can show it without a resource root.
const LOGO_DATA_URI =
  "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTUiIHZpZXdCb3g9IjAgMCAxNiAxNSIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPG1hc2sgaWQ9Im1hc2swXzExMV81MiIgc3R5bGU9Im1hc2stdHlwZTphbHBoYSIgbWFza1VuaXRzPSJ1c2VyU3BhY2VPblVzZSIgeD0iMCIgeT0iMCIgd2lkdGg9IjE2IiBoZWlnaHQ9IjE1Ij4KPHBhdGggZD0iTTE0LjA3NzcgMTMuOTg0QzE0Ljk0NSAxNC42MzQ1IDE2LjI0NTggMTQuMjAwOCAxNS4wNTMzIDEzLjAwODRDMTEuNDc2IDkuNTM5NDkgMTIuMjM0OSAwIDcuNzkwMzMgMEMzLjM0NTc5IDAgNC4xMDQ2MSA5LjUzOTQ5IDAuNTI3Mjk1IDEzLjAwODRDLTAuNzczNTQzIDE0LjMwOTIgMC42MzU2OTIgMTQuNjM0NSAxLjUwMjkzIDEzLjk4NEM0Ljg2MzQ0IDExLjcwNzYgNC42NDY2MyA3LjY5NjY0IDcuNzkwMzMgNy42OTY2NEMxMC45MzQgNy42OTY2NCAxMC43MTcyIDExLjcwNzYgMTQuMDc3NyAxMy45ODRaIiBmaWxsPSJibGFjayIvPgo8L21hc2s+CjxnIG1hc2s9InVybCgjbWFzazBfMTExXzUyKSI+CjxnIGZpbHRlcj0idXJsKCNmaWx0ZXIwX2ZfMTExXzUyKSI+CjxwYXRoIGQ9Ik0tMC42NTg5MDcgLTMuMjMwNkMtMC45MjI2NzkgLTAuOTA2NzgxIDEuMDc5ODYgMS4yMjg2MSAzLjgxMzg4IDEuNTM4OTRDNi41NDc5MSAxLjg0OTI3IDguOTc4MTEgMC4yMTcwMDkgOS4yNDE4OCAtMi4xMDY4MUM5LjUwNTY1IC00LjQzMDYzIDcuNTAzMTIgLTYuNTY2MDIgNC43NjkwOSAtNi44NzYzNUMyLjAzNTA2IC03LjE4NjY3IC0wLjM5NTEzNSAtNS41NTQ0MiAtMC42NTg5MDcgLTMuMjMwNloiIGZpbGw9IiNGRkU0MzIiLz4KPC9nPgo8ZyBmaWx0ZXI9InVybCgjZmlsdGVyMV9mXzExMV81MikiPgo8cGF0aCBkPSJNOS44ODIzMyA0LjM2NjQyQzEwLjU2NzMgNy4zMTU2OCAxMy41NjYgOS4xMzkwMiAxNi41ODAxIDguNDM4OTZDMTkuNTk0MiA3LjczODkxIDIxLjQ4MjMgNC43ODA1NiAyMC43OTczIDEuODMxMzFDMjAuMTEyMyAtMS4xMTc5NSAxNy4xMTM2IC0yLjk0MTI4IDE0LjA5OTUgLTIuMjQxMjNDMTEuMDg1NCAtMS41NDExOCA5LjE5NzMzIDEuNDE3MTcgOS44ODIzMyA0LjM2NjQyWiIgZmlsbD0iI0ZDNDEzRCIvPgo8L2c+CjxnIGZpbHRlcj0idXJsKCNmaWx0ZXIyX2ZfMTExXzUyKSI+CjxwYXRoIGQ9Ik0tOC4wNTI5MSA2LjM0NTEyQy03LjE4NzM2IDkuMzg4ODMgLTMuMjg5MjUgMTAuOTQ3MyAwLjY1Mzc3NCA5LjgyNTk4QzQuNTk2OCA4LjcwNDcgNy4wOTE1OCA1LjMyODI5IDYuMjI2MDMgMi4yODQ1OEM1LjM2MDQ4IC0wLjc1OTE0MiAxLjQ2MjM2IC0yLjMxNzU4IC0yLjQ4MDY2IC0xLjE5NjI5Qy02LjQyMzY4IC0wLjA3NTAwNDggLTguOTE4NDYgMy4zMDE0IC04LjA1MjkxIDYuMzQ1MTJaIiBmaWxsPSIjMDBCOTVDIi8+CjwvZz4KPGcgZmlsdGVyPSJ1cmwoI2ZpbHRlcjNfZl8xMTFfNTIpIj4KPHBhdGggZD0iTS04LjA1MjkxIDYuMzQ1MTJDLTcuMTg3MzYgOS4zODg4MyAtMy4yODkyNSAxMC45NDczIDAuNjUzNzc0IDkuODI1OThDNC41OTY4IDguNzA0NyA3LjA5MTU4IDUuMzI4MjkgNi4yMjYwMyAyLjI4NDU4QzUuMzYwNDggLTAuNzU5MTQyIDEuNDYyMzYgLTIuMzE3NTggLTIuNDgwNjYgLTEuMTk2MjlDLTYuNDIzNjggLTAuMDc1MDA0OCAtOC45MTg0NiAzLjMwMTQgLTguMDUyOTEgNi4zNDUxMloiIGZpbGw9IiMwMEI5NUMiLz4KPC9nPgo8ZyBmaWx0ZXI9InVybCgjZmlsdGVyNF9mXzExMV81MikiPgo8cGF0aCBkPSJNLTQuOTI0MDIgOC44Njc0NkMtMi43NTQyMSAxMS4wODM3IDAuOTgyNjkxIDEwLjk0MzggMy40MjI1NyA4LjU1NTA3QzUuODYyNDYgNi4xNjYzIDYuMDgxMzkgMi40MzMyMSAzLjkxMTU4IDAuMjE2OTYzQzEuNzQxNzcgLTEuOTk5MjggLTEuOTk1MTMgLTEuODU5NDIgLTQuNDM1MDEgMC41MjkzNDlDLTYuODc0ODkgMi45MTgxMiAtNy4wOTM4MyA2LjY1MTIyIC00LjkyNDAyIDguODY3NDZaIiBmaWxsPSIjMDBCOTVDIi8+CjwvZz4KPGcgZmlsdGVyPSJ1cmwoI2ZpbHRlcjVfZl8xMTFfNTIpIj4KPHBhdGggZD0iTTYuNDI4MTkgMTcuMjI2M0M3LjEwMTk3IDIwLjEyNzMgOS45MTI3OCAyMS45NTMgMTIuNzA2MyAyMS4zMDQyQzE1LjQ5OTggMjAuNjU1MyAxNy4yMTgyIDE3Ljc3NzcgMTYuNTQ0NCAxNC44NzY3QzE1Ljg3MDcgMTEuOTc1NyAxMy4wNTk5IDEwLjE1IDEwLjI2NjMgMTAuNzk4OEM3LjQ3MjgxIDExLjQ0NzcgNS43NTQ0MSAxNC4zMjUzIDYuNDI4MTkgMTcuMjI2M1oiIGZpbGw9IiMzMTg2RkYiLz4KPC9nPgo8ZyBmaWx0ZXI9InVybCgjZmlsdGVyNl9mXzExMV81MikiPgo8cGF0aCBkPSJNMS42NjUwOCAtNS45NDUzOUMwLjI1NDIxMyAtMi44MDI1NCAxLjc5NzggMC45NTE2MDkgNS4xMTI3NyAyLjQzOTczQzguNDI3NzQgMy45Mjc4NSAxMi4yNTg4IDIuNTg2NDIgMTMuNjY5NiAtMC41NTY0MzFDMTUuMDgwNSAtMy42OTkyOCAxMy41MzY5IC03LjQ1MzQzIDEwLjIyMiAtOC45NDE1NUM2LjkwNjk5IC0xMC40Mjk3IDMuMDc1OTQgLTkuMDg4MjQgMS42NjUwOCAtNS45NDUzOVoiIGZpbGw9IiNGQkJDMDQiLz4KPC9nPgo8ZyBmaWx0ZXI9InVybCgjZmlsdGVyN19mXzExMV81MikiPgo8cGF0aCBkPSJNLTIuMTE0MjggMjQuMzkwM0MtNS41Mjk4NCAyMy4wNDk2IDAuMzA3MjY2IDEyLjAxNzcgMS43NTg3NCA4LjMyMDM4QzMuMjEwMjQgNC42MjMwNCA3LjE1NTc2IDIuNzEyNzIgMTAuNTcxMyA0LjA1MzU3QzEzLjk4NjkgNS4zOTQ0MiAxOC4wMzU0IDEyLjc3OTYgMTYuNTgzOCAxNi40NzdDMTUuMTMyMyAyMC4xNzQzIDEuMzAxMjkgMjUuNzMxMSAtMi4xMTQyOCAyNC4zOTAzWiIgZmlsbD0iIzMxODZGRiIvPgo8L2c+CjxnIGZpbHRlcj0idXJsKCNmaWx0ZXI4X2ZfMTExXzUyKSI+CjxwYXRoIGQ9Ik0xOC41ODE0IDEwLjY1OThDMTcuNjY2OSAxMS43MjcgMTUuMjgwNiAxMS4xODI4IDEzLjI1MTQgOS40NDQxN0MxMS4yMjIyIDcuNzA1NTYgMTAuMzE4NSA1LjQzMDk3IDExLjIzMjkgNC4zNjM3QzEyLjE0NzMgMy4yOTY0NiAxNC41MzM2IDMuODQwNjkgMTYuNTYyOCA1LjU3OTI4QzE4LjU5MiA3LjMxNzg5IDE5LjQ5NTggOS41OTI0OSAxOC41ODE0IDEwLjY1OThaIiBmaWxsPSIjNzQ5QkZGIi8+CjwvZz4KPGcgZmlsdGVyPSJ1cmwoI2ZpbHRlcjlfZl8xMTFfNTIpIj4KPHBhdGggZD0iTTExLjc1NTIgNS4yMjcxNUMxNS41MTYyIDcuNzcxMjQgMTkuODQ3MSA3LjkzODM4IDIxLjQyODYgNS42MDA0NUMyMy4wMTAxIDMuMjYyNTMgMjEuMjQzMyAtMC42OTUxMjggMTcuNDgyMyAtMy4yMzkyMkMxMy43MjEzIC01Ljc4MzMxIDkuMzkwNDQgLTUuOTUwNDQgNy44MDg5NiAtMy42MTI1MkM2LjIyNzQ3IC0xLjI3NDU5IDcuOTk0MjggMi42ODMwNiAxMS43NTUyIDUuMjI3MTVaIiBmaWxsPSIjRkM0MTNEIi8+CjwvZz4KPGcgZmlsdGVyPSJ1cmwoI2ZpbHRlcjEwX2ZfMTExXzUyKSI+CjxwYXRoIGQ9Ik0tMC41OTIxNDkgMS4wODg5NkMtMS41MjM5IDMuMzM2NjMgLTEuMjE5NTkgNS41OTc5OSAwLjA4NzU0NTcgNi4xMzk4NUMxLjM5NDY4IDYuNjgxNzEgMy4yMDk2NiA1LjI5ODg4IDQuMTQxNDEgMy4wNTEyMUM1LjA3MzE2IDAuODAzNTQxIDQuNzY4ODUgLTEuNDU3ODIgMy40NjE3MSAtMS45OTk2OEMyLjE1NDU4IC0yLjU0MTU0IDAuMzM5NjAyIC0xLjE1ODcxIC0wLjU5MjE0OSAxLjA4ODk2WiIgZmlsbD0iI0ZGRUU0OCIvPgo8L2c+CjwvZz4KPGRlZnM+CjxmaWx0ZXIgaWQ9ImZpbHRlcjBfZl8xMTFfNTIiIHg9Ii0yLjEyODE3IiB5PSItOC4zNTk5OCIgd2lkdGg9IjEyLjgzOTMiIGhlaWdodD0iMTEuMzgzIiBmaWx0ZXJVbml0cz0idXNlclNwYWNlT25Vc2UiIGNvbG9yLWludGVycG9sYXRpb24tZmlsdGVycz0ic1JHQiI+CjxmZUZsb29kIGZsb29kLW9wYWNpdHk9IjAiIHJlc3VsdD0iQmFja2dyb3VuZEltYWdlRml4Ii8+CjxmZUJsZW5kIG1vZGU9Im5vcm1hbCIgaW49IlNvdXJjZUdyYXBoaWMiIGluMj0iQmFja2dyb3VuZEltYWdlRml4IiByZXN1bHQ9InNoYXBlIi8+CjxmZUdhdXNzaWFuQmx1ciBzdGREZXZpYXRpb249IjAuNzIyOTU5IiByZXN1bHQ9ImVmZmVjdDFfZm9yZWdyb3VuZEJsdXJfMTExXzUyIi8+CjwvZmlsdGVyPgo8ZmlsdGVyIGlkPSJmaWx0ZXIxX2ZfMTExXzUyIiB4PSIyLjc1MTY4IiB5PSItOS4zODA4OSIgd2lkdGg9IjI1LjE3NjMiIGhlaWdodD0iMjQuOTYiIGZpbHRlclVuaXRzPSJ1c2VyU3BhY2VPblVzZSIgY29sb3ItaW50ZXJwb2xhdGlvbi1maWx0ZXJzPSJzUkdCIj4KPGZlRmxvb2QgZmxvb2Qtb3BhY2l0eT0iMCIgcmVzdWx0PSJCYWNrZ3JvdW5kSW1hZ2VGaXgiLz4KPGZlQmxlbmQgbW9kZT0ibm9ybWFsIiBpbj0iU291cmNlR3JhcGhpYyIgaW4yPSJCYWNrZ3JvdW5kSW1hZ2VGaXgiIHJlc3VsdD0ic2hhcGUiLz4KPGZlR2F1c3NpYW5CbHVyIHN0ZERldmlhdGlvbj0iMy40OTUxMyIgcmVzdWx0PSJlZmZlY3QxX2ZvcmVncm91bmRCbHVyXzExMV81MiIvPgo8L2ZpbHRlcj4KPGZpbHRlciBpZD0iZmlsdGVyMl9mXzExMV81MiIgeD0iLTE0LjE2NjkiIHk9Ii03LjUwMTk2IiB3aWR0aD0iMjYuNTA2OCIgaGVpZ2h0PSIyMy42MzM4IiBmaWx0ZXJVbml0cz0idXNlclNwYWNlT25Vc2UiIGNvbG9yLWludGVycG9sYXRpb24tZmlsdGVycz0ic1JHQiI+CjxmZUZsb29kIGZsb29kLW9wYWNpdHk9IjAiIHJlc3VsdD0iQmFja2dyb3VuZEltYWdlRml4Ii8+CjxmZUJsZW5kIG1vZGU9Im5vcm1hbCIgaW49IlNvdXJjZUdyYXBoaWMiIGluMj0iQmFja2dyb3VuZEltYWdlRml4IiByZXN1bHQ9InNoYXBlIi8+CjxmZUdhdXNzaWFuQmx1ciBzdGREZXZpYXRpb249IjIuOTcxMTkiIHJlc3VsdD0iZWZmZWN0MV9mb3JlZ3JvdW5kQmx1cl8xMTFfNTIiLz4KPC9maWx0ZXI+CjxmaWx0ZXIgaWQ9ImZpbHRlcjNfZl8xMTFfNTIiIHg9Ii0xNC4xNjY5IiB5PSItNy41MDE5NiIgd2lkdGg9IjI2LjUwNjgiIGhlaWdodD0iMjMuNjMzOCIgZmlsdGVyVW5pdHM9InVzZXJTcGFjZU9uVXNlIiBjb2xvci1pbnRlcnBvbGF0aW9uLWZpbHRlcnM9InNSR0IiPgo8ZmVGbG9vZCBmbG9vZC1vcGFjaXR5PSIwIiByZXN1bHQ9IkJhY2tncm91bmRJbWFnZUZpeCIvPgo8ZmVCbGVuZCBtb2RlPSJub3JtYWwiIGluPSJTb3VyY2VHcmFwaGljIiBpbjI9IkJhY2tncm91bmRJbWFnZUZpeCIgcmVzdWx0PSJzaGFwZSIvPgo8ZmVHYXVzc2lhbkJsdXIgc3RkRGV2aWF0aW9uPSIyLjk3MTE5IiByZXN1bHQ9ImVmZmVjdDFfZm9yZWdyb3VuZEJsdXJfMTExXzUyIi8+CjwvZmlsdGVyPgo8ZmlsdGVyIGlkPSJmaWx0ZXI0X2ZfMTExXzUyIiB4PSItMTIuMzYwNyIgeT0iLTcuMjk5ODEiIHdpZHRoPSIyMy43MDkiIGhlaWdodD0iMjMuNjg0NiIgZmlsdGVyVW5pdHM9InVzZXJTcGFjZU9uVXNlIiBjb2xvci1pbnRlcnBvbGF0aW9uLWZpbHRlcnM9InNSR0IiPgo8ZmVGbG9vZCBmbG9vZC1vcGFjaXR5PSIwIiByZXN1bHQ9IkJhY2tncm91bmRJbWFnZUZpeCIvPgo8ZmVCbGVuZCBtb2RlPSJub3JtYWwiIGluPSJTb3VyY2VHcmFwaGljIiBpbjI9IkJhY2tncm91bmRJbWFnZUZpeCIgcmVzdWx0PSJzaGFwZSIvPgo8ZmVHYXVzc2lhbkJsdXIgc3RkRGV2aWF0aW9uPSIyLjk3MTE5IiByZXN1bHQ9ImVmZmVjdDFfZm9yZWdyb3VuZEJsdXJfMTExXzUyIi8+CjwvZmlsdGVyPgo8ZmlsdGVyIGlkPSJmaWx0ZXI1X2ZfMTExXzUyIiB4PSIwLjYzNDk2MiIgeT0iNS4wMjA5NSIgd2lkdGg9IjIxLjcwMjciIGhlaWdodD0iMjIuMDYxNiIgZmlsdGVyVW5pdHM9InVzZXJTcGFjZU9uVXNlIiBjb2xvci1pbnRlcnBvbGF0aW9uLWZpbHRlcnM9InNSR0IiPgo8ZmVGbG9vZCBmbG9vZC1vcGFjaXR5PSIwIiByZXN1bHQ9IkJhY2tncm91bmRJbWFnZUZpeCIvPgo8ZmVCbGVuZCBtb2RlPSJub3JtYWwiIGluPSJTb3VyY2VHcmFwaGljIiBpbjI9IkJhY2tncm91bmRJbWFnZUZpeCIgcmVzdWx0PSJzaGFwZSIvPgo8ZmVHYXVzc2lhbkJsdXIgc3RkRGV2aWF0aW9uPSIyLjgyMzUxIiByZXN1bHQ9ImVmZmVjdDFfZm9yZWdyb3VuZEJsdXJfMTExXzUyIi8+CjwvZmlsdGVyPgo8ZmlsdGVyIGlkPSJmaWx0ZXI2X2ZfMTExXzUyIiB4PSItMy45NzU0NyIgeT0iLTE0LjY2NjYiIHdpZHRoPSIyMy4yODU3IiBoZWlnaHQ9IjIyLjgzMTMiIGZpbHRlclVuaXRzPSJ1c2VyU3BhY2VPblVzZSIgY29sb3ItaW50ZXJwb2xhdGlvbi1maWx0ZXJzPSJzUkdCIj4KPGZlRmxvb2QgZmxvb2Qtb3BhY2l0eT0iMCIgcmVzdWx0PSJCYWNrZ3JvdW5kSW1hZ2VGaXgiLz4KPGZlQmxlbmQgbW9kZT0ibm9ybWFsIiBpbj0iU291cmNlR3JhcGhpYyIgaW4yPSJCYWNrZ3JvdW5kSW1hZ2VGaXgiIHJlc3VsdD0ic2hhcGUiLz4KPGZlR2F1c3NpYW5CbHVyIHN0ZERldmlhdGlvbj0iMi41NTg5IiByZXN1bHQ9ImVmZmVjdDFfZm9yZWdyb3VuZEJsdXJfMTExXzUyIi8+CjwvZmlsdGVyPgo8ZmlsdGVyIGlkPSJmaWx0ZXI3X2ZfMTExXzUyIiB4PSItNy43NDA3IiB5PSItMC45NDU0MDgiIHdpZHRoPSIyOS4xOTgyIiBoZWlnaHQ9IjMwLjExMDUiIGZpbHRlclVuaXRzPSJ1c2VyU3BhY2VPblVzZSIgY29sb3ItaW50ZXJwb2xhdGlvbi1maWx0ZXJzPSJzUkdCIj4KPGZlRmxvb2QgZmxvb2Qtb3BhY2l0eT0iMCIgcmVzdWx0PSJCYWNrZ3JvdW5kSW1hZ2VGaXgiLz4KPGZlQmxlbmQgbW9kZT0ibm9ybWFsIiBpbj0iU291cmNlR3JhcGhpYyIgaW4yPSJCYWNrZ3JvdW5kSW1hZ2VGaXgiIHJlc3VsdD0ic2hhcGUiLz4KPGZlR2F1c3NpYW5CbHVyIHN0ZERldmlhdGlvbj0iMi4yODUyIiByZXN1bHQ9ImVmZmVjdDFfZm9yZWdyb3VuZEJsdXJfMTExXzUyIi8+CjwvZmlsdGVyPgo8ZmlsdGVyIGlkPSJmaWx0ZXI4X2ZfMTExXzUyIiB4PSI2Ljc4NjQxIiB5PSItMC4yNzIzMSIgd2lkdGg9IjE2LjI0MTUiIGhlaWdodD0iMTUuNTY4MSIgZmlsdGVyVW5pdHM9InVzZXJTcGFjZU9uVXNlIiBjb2xvci1pbnRlcnBvbGF0aW9uLWZpbHRlcnM9InNSR0IiPgo8ZmVGbG9vZCBmbG9vZC1vcGFjaXR5PSIwIiByZXN1bHQ9IkJhY2tncm91bmRJbWFnZUZpeCIvPgo8ZmVCbGVuZCBtb2RlPSJub3JtYWwiIGluPSJTb3VyY2VHcmFwaGljIiBpbjI9IkJhY2tncm91bmRJbWFnZUZpeCIgcmVzdWx0PSJzaGFwZSIvPgo8ZmVHYXVzc2lhbkJsdXIgc3RkRGV2aWF0aW9uPSIyLjA0NDg1IiByZXN1bHQ9ImVmZmVjdDFfZm9yZWdyb3VuZEJsdXJfMTExXzUyIi8+CjwvZmlsdGVyPgo8ZmlsdGVyIGlkPSJmaWx0ZXI5X2ZfMTExXzUyIiB4PSIzLjc3NTI2IiB5PSItOC43MTY5MyIgd2lkdGg9IjIxLjY4NyIgaGVpZ2h0PSIxOS40MjEyIiBmaWx0ZXJVbml0cz0idXNlclNwYWNlT25Vc2UiIGNvbG9yLWludGVycG9sYXRpb24tZmlsdGVycz0ic1JHQiI+CjxmZUZsb29kIGZsb29kLW9wYWNpdHk9IjAiIHJlc3VsdD0iQmFja2dyb3VuZEltYWdlRml4Ii8+CjxmZUJsZW5kIG1vZGU9Im5vcm1hbCIgaW49IlNvdXJjZUdyYXBoaWMiIGluMj0iQmFja2dyb3VuZEltYWdlRml4IiByZXN1bHQ9InNoYXBlIi8+CjxmZUdhdXNzaWFuQmx1ciBzdGREZXZpYXRpb249IjEuNzI3MTIiIHJlc3VsdD0iZWZmZWN0MV9mb3JlZ3JvdW5kQmx1cl8xMTFfNTIiLz4KPC9maWx0ZXI+CjxmaWx0ZXIgaWQ9ImZpbHRlcjEwX2ZfMTExXzUyIiB4PSItNS40MDcyNyIgeT0iLTYuMzkyMzgiIHdpZHRoPSIxNC4zNjM5IiBoZWlnaHQ9IjE2LjkyNTQiIGZpbHRlclVuaXRzPSJ1c2VyU3BhY2VPblVzZSIgY29sb3ItaW50ZXJwb2xhdGlvbi1maWx0ZXJzPSJzUkdCIj4KPGZlRmxvb2QgZmxvb2Qtb3BhY2l0eT0iMCIgcmVzdWx0PSJCYWNrZ3JvdW5kSW1hZ2VGaXgiLz4KPGZlQmxlbmQgbW9kZT0ibm9ybWFsIiBpbj0iU291cmNlR3JhcGhpYyIgaW4yPSJCYWNrZ3JvdW5kSW1hZ2VGaXgiIHJlc3VsdD0ic2hhcGUiLz4KPGZlR2F1c3NpYW5CbHVyIHN0ZERldmlhdGlvbj0iMi4xMzc2IiByZXN1bHQ9ImVmZmVjdDFfZm9yZWdyb3VuZEJsdXJfMTExXzUyIi8+CjwvZmlsdGVyPgo8L2RlZnM+Cjwvc3ZnPgo=";

export class WarningViewProvider implements vscode.WebviewViewProvider {
  private view: vscode.WebviewView | undefined;
  private suggestion: UsageSuggestion | undefined;
  private urgency: UrgencyLevel = "moderate";
  private callbacks: WarningCallbacks | undefined;
  private dismissTimer: ReturnType<typeof setTimeout> | undefined;

  resolveWebviewView(view: vscode.WebviewView): void {
    this.view = view;
    view.webview.options = { enableScripts: true };

    view.onDidDispose(() => {
      // The view is torn down when the when-clause turns false; drop the stale ref
      // so the next show() re-reveals (and re-resolves) it instead of posting to a
      // disposed webview.
      if (this.view === view) {
        this.clearDismissTimer();
        this.view = undefined;
      }
    });

    view.webview.onDidReceiveMessage((message: { command: string }) => {
      switch (message.command) {
        case "cancel":
          void this.hide();
          break;
        case "openDashboard":
          this.callbacks?.onOpenDashboard();
          break;
      }
    });

    view.webview.html = this.getHtml(view.webview);
  }

  /**
   * Reveal the warning for the given suggestion. Sets the context key so the
   * container becomes available, then either refreshes an already-resolved view
   * or focuses the view id to reveal it (which triggers resolveWebviewView and
   * renders the stored suggestion).
   */
  async show(
    suggestion: UsageSuggestion,
    urgency: UrgencyLevel,
    callbacks: WarningCallbacks,
  ): Promise<void> {
    this.clearDismissTimer();
    this.dismissTimer = setTimeout(() => {
      void this.hide();
    }, 60_000);
    this.suggestion = suggestion;
    this.urgency = urgency;
    this.callbacks = callbacks;

    await vscode.commands.executeCommand("setContext", WARNING_ACTIVE_CONTEXT, true);

    if (this.view) {
      this.view.webview.html = this.getHtml(this.view.webview);
      this.view.show(true);
    } else {
      await vscode.commands.executeCommand(`${WARNING_VIEW_ID}.focus`);
    }
  }

  /** Dismiss the warning: flip the context key so the view and its container hide. */
  private async hide(): Promise<void> {
    this.clearDismissTimer();
    this.suggestion = undefined;
    this.view = undefined;
    await vscode.commands.executeCommand("setContext", WARNING_ACTIVE_CONTEXT, false);
  }

  private clearDismissTimer(): void {
    if (this.dismissTimer !== undefined) {
      clearTimeout(this.dismissTimer);
      this.dismissTimer = undefined;
    }
  }

  private getHtml(webview: vscode.Webview): string {
    const s = this.suggestion;
    if (!s) {
      return this.wrapHtml(webview, `<p class="empty">No active usage warning.</p>`);
    }

    const color = URGENCY_COLOR[this.urgency];
    const label = "Gemini";
    const pct = Math.max(0, Math.min(100, Math.round(s.percent)));

    // Ring geometry: an SVG circle whose visible arc is `pct` of its circumference.
    const r = 52;
    const circumference = 2 * Math.PI * r;
    const arc = (pct / 100) * circumference;

    const switchRow = s.switchModel
      ? `<div class="rec">${ICON.swap}<span>Switch to <strong>${escapeHtml(s.switchModel)}</strong>, which still has quota</span></div>`
      : "";

    // "Resets in 3h 7m" / "Resets on Tuesday ..." -> "Usage will reset in 3h 7m."
    const resetSentence = "Usage will " + formatResetLabel(s.resetsIn).replace(/^Resets/, "reset") + ".";

    return this.wrapHtml(webview, `
      <div class="warn">
        <button class="close" data-command="cancel" title="Dismiss" aria-label="Dismiss">${ICON.close}</button>

        <div class="brand">
          <img class="brand-logo" src="${LOGO_DATA_URI}" alt="" />
          <div class="brand-title">
            <div class="brand-name">${escapeHtml(label)}</div>
            <div class="brand-sub">Usage Monitor</div>
          </div>
        </div>

        <div class="ring-wrap">
          <svg class="ring" viewBox="0 0 120 120" width="132" height="132" aria-hidden="true">
            <circle class="ring-track" cx="60" cy="60" r="${r}" fill="none" stroke-width="10"/>
            <circle cx="60" cy="60" r="${r}" fill="none" stroke="${color}" stroke-width="10"
                    stroke-linecap="round" stroke-dasharray="${arc.toFixed(2)} ${circumference.toFixed(2)}"
                    transform="rotate(-90 60 60)"/>
          </svg>
          <div class="ring-center">
            <div class="ring-pct">${pct}%</div>
            <div class="ring-label">${escapeHtml(s.label)}</div>
          </div>
        </div>

        <div class="rec-head"><span>Ways to extend your usage</span></div>

        <div class="recs">
          ${switchRow}
          <div class="rec">${ICON.gauge}<span>${escapeHtml(s.effortAdvice)}</span></div>
        </div>

        <div class="reset-box">
          ${ICON.clock}<span>${escapeHtml(resetSentence)}</span>
        </div>

        <div class="divider"></div>

        <div class="footer">
          <span class="source">${ICON.chart}<span>Source: ${escapeHtml(label)} Usage Monitor</span></span>
          <div class="footer-actions">
            <button class="secondary" data-command="openDashboard">Open Dashboard</button>
            <button class="primary" data-command="cancel">OK</button>
          </div>
        </div>
      </div>
    `);
  }

  private wrapHtml(webview: vscode.Webview, body: string): string {
    // Nonce-gated script + strict CSP; buttons are wired with addEventListener
    // (not inline onclick), the reliable VS Code webview pattern.
    const nonce = getNonce();
    return `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src data:; style-src ${webview.cspSource} 'unsafe-inline'; script-src 'nonce-${nonce}';">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    body {
      font-family: var(--vscode-font-family);
      color: var(--vscode-foreground);
      background: var(--vscode-sideBar-background, var(--vscode-editor-background));
      padding: 12px 14px;
    }
    .warn { width: 100%; position: relative; }
    .empty { opacity: 0.7; font-size: 13px; }
    /* Centered brand block: real product icon above a two-line "<PRODUCT>" / "Usage Monitor" title. */
    .brand {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 10px;
      text-align: center;
      padding: 2px 0;
    }
    /* The full-color extension icon (data URI), sized down from its native resolution so it
       stays crisp; no tinting, so it renders in its original brand colors. */
    .brand-logo { display: block; width: 44px; height: 44px; }
    .brand-title { display: flex; flex-direction: column; align-items: center; gap: 2px; }
    .brand-name {
      font-size: 22px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      line-height: 1.1;
      color: var(--vscode-sideBarTitle-foreground, var(--vscode-foreground));
    }
    .brand-sub {
      font-size: 16px;
      font-weight: 600;
      line-height: 1.1;
      color: var(--vscode-sideBarTitle-foreground, var(--vscode-foreground));
    }
    /* Dismiss control pinned to the top-right corner, clear of the centered brand. */
    .close {
      position: absolute;
      top: 0;
      right: 0;
      background: transparent;
      border: none;
      color: var(--vscode-descriptionForeground, var(--vscode-foreground));
      cursor: pointer;
      padding: 3px;
      opacity: 0.7;
      border-radius: 4px;
    }
    .close:hover { opacity: 1; background: var(--vscode-toolbar-hoverBackground, rgba(128,128,128,0.2)); }
    .close svg { display: block; width: 16px; height: 16px; }
    .divider {
      border-top: 1px solid var(--vscode-widget-border, rgba(128,128,128,0.25));
      margin: 12px 0;
    }
    /* Small, centered section heading below the ring (previously the large hero heading). */
    .rec-head {
      font-size: 13px;
      font-weight: 600;
      line-height: 1.3;
      text-align: center;
      opacity: 0.85;
      margin: 20px 0 12px;
    }
    .recs {
      display: flex;
      flex-direction: column;
      gap: 10px;
      width: fit-content;
      max-width: 100%;
      margin: 0 auto;
    }
    .rec {
      display: flex;
      align-items: flex-start;
      gap: 9px;
      font-size: 13px;
      line-height: 1.4;
    }
    .rec svg { flex-shrink: 0; width: 18px; height: 18px; margin-top: 1px; }
    .icon-swap { color: var(--vscode-charts-blue, #4aa5f0); }
    .icon-gauge { color: var(--vscode-charts-green, #3fb950); }
    .icon-clock { color: var(--vscode-charts-blue, #4aa5f0); }
    .icon-chart { color: var(--vscode-descriptionForeground, #8b949e); }
    .rec strong { font-weight: 700; }
    /* Ring centered below the brand block. */
    .ring-wrap { position: relative; width: 132px; height: 132px; margin: 16px auto 0; }
    .ring-track { stroke: rgba(128,128,128,0.25); }
    .ring-center {
      position: absolute;
      inset: 0;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      pointer-events: none;
    }
    .ring-pct { font-size: 30px; font-weight: 700; line-height: 1; }
    .ring-label { font-size: 12px; opacity: 0.7; margin-top: 4px; }
    /* Extra breathing room between the ring and the reset indicator. */
    .reset-box {
      display: flex;
      align-items: flex-start;
      gap: 9px;
      padding: 11px 12px;
      margin-top: 20px;
      border: 1px solid var(--vscode-widget-border, rgba(128,128,128,0.25));
      border-radius: 8px;
      font-size: 13px;
      line-height: 1.4;
    }
    .reset-box svg { flex-shrink: 0; width: 18px; height: 18px; margin-top: 1px; }
    .footer {
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    .source {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 12px;
      opacity: 0.8;
    }
    .source svg { width: 16px; height: 16px; }
    .footer-actions { display: flex; gap: 8px; }
    .footer-actions button { flex: 1; }
    button {
      padding: 7px 12px;
      border: none;
      border-radius: 6px;
      cursor: pointer;
      font-size: 12.5px;
      font-family: var(--vscode-font-family);
    }
    button.primary { color: var(--vscode-button-foreground); background: var(--vscode-button-background); }
    button.primary:hover { background: var(--vscode-button-hoverBackground); }
    button.secondary { color: var(--vscode-button-secondaryForeground); background: var(--vscode-button-secondaryBackground); }
    button.secondary:hover { background: var(--vscode-button-secondaryHoverBackground); }
  </style>
</head>
<body>
  ${body}
  <script nonce="${nonce}">
    const vscode = acquireVsCodeApi();
    document.querySelectorAll('[data-command]').forEach(function (el) {
      el.addEventListener('click', function () {
        vscode.postMessage({ command: el.getAttribute('data-command') });
      });
    });
  </script>
</body>
</html>`;
  }
}

// Inline SVG icons (self-contained; no font/resource loading). Line-style,
// currentColor, so CSS classes tint them.
const ICON = {
  warning:
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
  close:
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>',
  swap:
    '<span class="icon-swap"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="17 1 21 5 17 9"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/><polyline points="7 23 3 19 7 15"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/></svg></span>',
  gauge:
    '<span class="icon-gauge"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 14a2 2 0 1 0 0-4 2 2 0 0 0 0 4z"/><path d="m13.4 12.6 3.6-3.6"/><path d="M3.5 18a9 9 0 1 1 17 0"/></svg></span>',
  clock:
    '<span class="icon-clock"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><polyline points="12 7 12 12 15 14"/></svg></span>',
  chart:
    '<span class="icon-chart"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="6" y1="20" x2="6" y2="13"/><line x1="12" y1="20" x2="12" y2="8"/><line x1="18" y1="20" x2="18" y2="11"/></svg></span>',
};

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

/** Random nonce for the webview's Content-Security-Policy script allowance. */
function getNonce(): string {
  let text = "";
  const possible = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
  for (let i = 0; i < 32; i++) {
    text += possible.charAt(Math.floor(Math.random() * possible.length));
  }
  return text;
}
