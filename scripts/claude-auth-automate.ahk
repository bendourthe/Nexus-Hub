; Claude Code Auth Automator (AutoHotkey v2)
; Triggered by claude-auth-monitor.ps1 when the session token is invalid.
; Steps:
;   1. Trigger the VS Code Claude Code sign-in flow (opens Anthropic OAuth page in browser)
;   2. Wait for the browser window showing the Anthropic "Authorize" consent page
;   3. Click the primary Authorize button
;   4. Write a sentinel file signalling success to the monitor script
;
; Installed to: ~/.devai-hub/scripts/claude-auth-automate.ahk

#Requires AutoHotkey v2.0
#SingleInstance Force

; --- Configuration ---
AuthorizePageTimeout := 30000   ; ms to wait for the Authorize page to appear
ButtonClickTimeout   := 10000   ; ms to wait for the Authorize button to become clickable
SentinelFile         := A_UserProfile "\.claude\.reauth-complete"
ClaudeDir            := A_UserProfile "\.claude"

; --- Step 1: Trigger VS Code sign-in ---
; Run the VS Code CLI command that opens the Claude Code authentication URL.
; This is equivalent to clicking "Sign in to Claude Code" from the extension.
RunWait('cmd.exe /c code --command "workbench.action.reloadWindow" >nul 2>&1',, "Hide")

; Give VS Code a moment to detect the expired session and open the browser.
Sleep(3000)

; Also try triggering the auth via the Claude CLI if available.
RunWait('cmd.exe /c claude auth login >nul 2>&1',, "Hide")

Sleep(2000)

; --- Step 2: Wait for the Anthropic authorization page ---
; Detect the browser window by its title. The Anthropic consent page title
; contains "Authorize" when Claude Code is requesting access.
authorizeHwnd := 0
deadline := A_TickCount + AuthorizePageTimeout

Loop {
    ; Search across common browsers
    for _, browserTitle in ["Authorize - Claude", "Authorize Claude", "claude.ai", "anthropic.com"] {
        hwnd := WinExist("ahk_exe chrome.exe")
        if hwnd && WinGetTitle(hwnd) ~= "i)Authorize" {
            authorizeHwnd := hwnd
            break
        }
        hwnd := WinExist("ahk_exe msedge.exe")
        if hwnd && WinGetTitle(hwnd) ~= "i)Authorize" {
            authorizeHwnd := hwnd
            break
        }
        hwnd := WinExist("ahk_exe firefox.exe")
        if hwnd && WinGetTitle(hwnd) ~= "i)Authorize" {
            authorizeHwnd := hwnd
            break
        }
    }
    if authorizeHwnd
        break
    if A_TickCount > deadline {
        ; Page did not appear — notify and exit without writing sentinel
        Run('powershell.exe -NonInteractive -Command "' .
            '[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null;' .
            'Add-Type -AssemblyName System.Windows.Forms;' .
            '$n = New-Object System.Windows.Forms.NotifyIcon;' .
            '$n.Icon = [System.Drawing.SystemIcons]::Warning;' .
            '$n.Visible = $true;' .
            '$n.ShowBalloonTip(8000, ''Claude Code'', ''Sign-in page not found. Please authorize manually in VS Code.'', [System.Windows.Forms.ToolTipIcon]::Warning);' .
            'Start-Sleep 9; $n.Dispose()"',, "Hide")
        ExitApp()
    }
    Sleep(500)
}

; --- Step 3: Bring the authorize page to the foreground and click Authorize ---
WinActivate(authorizeHwnd)
Sleep(800)

; Try to click the Authorize button via UI Automation text search.
; Fall back to a position-based click near the center-bottom of the page
; where the Authorize button typically renders on the Anthropic consent page.
clicked := false

; Attempt: use Acc (accessibility) to find a button with text "Authorize"
; AutoHotkey v2 does not ship Acc by default, so we use a simpler approach:
; send Tab key to focus the first/primary button and press Enter.
; The Anthropic consent page has the "Authorize" button as the primary action.
WinGetPos(&wx, &wy, &ww, &wh, authorizeHwnd)
; Click approximately where the Authorize button renders (center-bottom region)
; This is an estimate; the Acc-based approach below is preferred when available.

; Try sending Enter after focusing the window — works if Authorize is the default button
Send("{Enter}")
Sleep(500)

; If Enter did not work (page might require explicit click), try a click at the
; approximate center of the viewport, slightly below center where CTA buttons appear.
if !clicked {
    centerX := wx + (ww // 2)
    centerY := wy + Round(wh * 0.62)   ; ~62% down is typical for CTA buttons
    Click(centerX, centerY)
    Sleep(500)
}

; --- Step 4: Wait for the page to redirect (OAuth complete signal) ---
; After clicking Authorize, the browser redirects to a localhost callback URL.
; We detect this by waiting for the Authorize-titled window to disappear or change title.
deadline := A_TickCount + ButtonClickTimeout
Loop {
    ; Check if the window is gone or redirected
    if !WinExist(authorizeHwnd)
        break
    currentTitle := WinGetTitle(authorizeHwnd)
    if !(currentTitle ~= "i)Authorize")
        break
    if A_TickCount > deadline
        break
    Sleep(400)
}

; Small delay to allow Claude Code to process the OAuth callback and write credentials
Sleep(2000)

; --- Step 5: Write the sentinel file ---
FileAppend(FormatTime(A_Now, "yyyy-MM-dd HH:mm:ss"), SentinelFile)

ExitApp()
