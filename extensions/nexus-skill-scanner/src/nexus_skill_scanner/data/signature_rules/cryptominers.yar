// Cryptominer signature rules (detection class 14).
//
// Re-authored from public miner-configuration knowledge. A skill that quietly
// mines cryptocurrency on the host is malware regardless of how it is packaged;
// these rules key on the network and CLI surface a miner needs, not on any
// vendor's bundled signature file.

rule stratum_mining_pool
{
    meta:
        severity = "high"
        description = "Cryptocurrency miner: connects to a stratum mining pool."
    strings:
        $tcp = "stratum+tcp://" nocase
        $ssl = "stratum+ssl://" nocase
    condition:
        any of them
}

rule xmrig_miner_cli
{
    meta:
        severity = "high"
        description = "Cryptocurrency miner: XMRig-style configuration or invocation."
    strings:
        $name = "xmrig" nocase
        $donate = /--donate-level\s+\d/ nocase
        $cpu = /--cpu-priority\s+\d/ nocase
        $algo = /--algo\s+(rx\/0|cn\/|argon2)/ nocase
    condition:
        2 of them
}

rule browser_miner_loader
{
    meta:
        severity = "medium"
        description = "In-browser cryptominer loader (CoinHive-style API surface)."
    strings:
        $coinhive = /coinhive/ nocase
        $cryptonight = /cryptonight/ nocase
        $ctor = /new\s+\w*Miner\s*\(/
        $start = ".start("
    condition:
        $coinhive or $cryptonight or ($ctor and $start)
}
