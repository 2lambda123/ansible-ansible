#!powershell

#Requires -Module Ansible.ModuleUtils.Legacy
#Requires -Module Ansible.ModuleUtils.LinkUtil

$params = Parse-Args $args

$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateset "absent","present"
$src = Get-AnsibleParam -obj $params -name "src" -type "path" -failifempty $true
$target = Get-AnsibleParam -obj $params -name "target" -type "path" -failifempty $($state -eq "present")

$result = @{
    changed = $false
}

Import-LinkUtil

if ($state -eq "absent") {
    if (Test-AnsiblePath -Path $src) {
        Remove-Link -link_path $src
        $result.changed = $true
    }
} else {
    if (-not (Test-AnsiblePath -Path $src)) {
        New-Link -link_path $src -link_target $target -link_type "link"
        $result.changed = $true
    }
}

Exit-Json -obj $result
