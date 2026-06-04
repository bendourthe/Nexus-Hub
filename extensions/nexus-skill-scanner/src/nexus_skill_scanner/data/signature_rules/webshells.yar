// Web-shell signature rules (detection class 14).
//
// Re-authored from public web-shell analysis. These describe the *behavioral
// shape* of a shell (evaluate attacker-controlled request input, often after
// an obfuscation decode) rather than reproducing any external rule set's
// signatures. Severities sit at HIGH: a genuine match in an executable script
// is a strong malicious signal, but the module is opt-in and adjudicated by the
// skill-security-scan skill before any gate decision.

rule php_eval_request_input
{
    meta:
        severity = "high"
        description = "PHP web shell: evaluates attacker-controlled request input (remote code execution)."
    strings:
        $eval = /\beval\s*\(\s*\$_(GET|POST|REQUEST|COOKIE)/ nocase
        $assert = /\bassert\s*\(\s*\$_(GET|POST|REQUEST)/ nocase
        $create_fn = /create_function\s*\(\s*['"]?\s*,\s*\$_(GET|POST|REQUEST)/ nocase
    condition:
        any of them
}

rule php_obfuscated_eval
{
    meta:
        severity = "high"
        description = "PHP web shell: eval of a base64/gzip-decoded payload (obfuscated remote code execution)."
    strings:
        $b64 = "base64_decode(" nocase
        $gz = "gzinflate(" nocase
        $rot = "str_rot13(" nocase
        $eval = /\beval\s*\(/ nocase
    condition:
        $eval and ($b64 or $gz or $rot)
}

rule php_system_request_input
{
    meta:
        severity = "high"
        description = "PHP web shell: passes request input straight to a command executor."
    strings:
        $a = /\b(system|shell_exec|passthru|popen|proc_open)\s*\(\s*\$_(GET|POST|REQUEST)/ nocase
    condition:
        any of them
}

rule jsp_runtime_exec_request
{
    meta:
        severity = "high"
        description = "JSP web shell: Runtime.exec driven by a request parameter."
    strings:
        $exec = "Runtime.getRuntime().exec("
        $param = /request\.getParameter\s*\(/
    condition:
        all of them
}

rule asp_eval_request
{
    meta:
        severity = "high"
        description = "ASP/ASPX web shell: Eval/Execute of Request input."
    strings:
        $a = /\b(Eval|Execute|ExecuteGlobal)\s*\(\s*Request/ nocase
        $b = /eval\s*\(\s*Request\.(Item|Form|QueryString)/ nocase
    condition:
        any of them
}
