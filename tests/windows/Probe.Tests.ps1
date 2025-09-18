# Pester tests for Get-CogSecEndpointState.ps1
# Run on Windows PowerShell 5.1+ or pwsh 7+.

$ErrorActionPreference = 'Stop'

$script:ProbePath = Join-Path (Split-Path -Parent (Split-Path -Parent $PSCommandPath)) 'cogsec/collectors/Get-CogSecEndpointState.ps1'

Describe 'Get-CogSecEndpointState probe' {
    It 'Emits valid JSON with required fields (quick mode)' {
        $json = & powershell -NoProfile -ExecutionPolicy Bypass -File $script:ProbePath -Quick -JsonPath - -Diagnostics
        $obj = $json | ConvertFrom-Json
        $obj | Should -Not -BeNullOrEmpty
        $obj.schema_version | Should -Match '^1\\.1\\.'
        foreach($f in 'host','timestamp','os','cpu','mem','disk','firewall_enabled','rdp_enabled','controls','patch'){
            $obj.PSObject.Properties.Name | Should -Contain $f
        }
        $obj.controls.PSObject.Properties.Name | Should -Contain 'av_vendor'
        $obj.patch.PSObject.Properties.Name   | Should -Contain 'required_total'
    }

    It 'Includes patch compliance fields when RequiredKBs provided' {
        $json = & powershell -NoProfile -ExecutionPolicy Bypass -File $script:ProbePath -RequiredKBs KB0000001,KB0000002 -JsonPath -
        $obj = $json | ConvertFrom-Json
        $obj.patch | Should -Not -BeNullOrEmpty
        $obj.patch.PSObject.Properties.Name | Should -Contain 'missing'
        $obj.patch.PSObject.Properties.Name | Should -Contain 'missing_count'
    }
}
