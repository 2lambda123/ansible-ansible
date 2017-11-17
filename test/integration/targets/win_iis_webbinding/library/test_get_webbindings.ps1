$params = Parse-Args -arguments $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

$name = Get-AnsibleParam $params -name "name" -type str -failifempty $true -aliases 'website'
#$state = Get-AnsibleParam $params "state" -default "present" -validateSet "present","absent"
$host_header = Get-AnsibleParam $params -name "host_header" -type str
$protocol = Get-AnsibleParam $params -name "protocol" -type str -default 'http'
$port = Get-AnsibleParam $params -name "port" -type int -default '80'
$ip = Get-AnsibleParam $params -name "ip" -default '*'
$certificateHash = Get-AnsibleParam $params -name "certificate_hash" -type str
$certificateStoreName = Get-AnsibleParam $params -name "certificate_store_name" -type str
$sslFlags = Get-AnsibleParam $params -name "ssl_flags" -type int -default '0' -ValidateSet '0','1','2','3'

$result = @{
  changed = $false
}

function Create-BindingInfo {
    $ht = @{
        'bindingInformation' = $args[0].bindingInformation
        'ip' = $args[0].bindingInformation.split(':')[0]
        'port' = $args[0].bindingInformation.split(':')[1]
        'isDsMapperEnabled' = $args[0].isDsMapperEnabled
        'protocol' = $args[0].protocol
        'certificateStoreName' = $args[0].certificateStoreName
        'certificateHash' = $args[0].certificateHash
    }

    #handle sslflag support
    If ([version][System.Environment]::OSVersion.Version -lt [version]'6.2')
    {
        $ht.sslFlags = 'not supported'
    }
    Else
    {
        $ht.sslFlags = $args[0].sslFlags
    }

    Return $ht
}

# Used instead of get-webbinding to ensure we always return a single binding
# pass it $binding_parameters hashtable
function Get-SingleWebBinding {
    $bind_search_splat = @{
        'name' = $args[0].name
        'protocol' = $args[0].protocol
        'port' = $args[0].port
        'ip' = $args[0].ip
        'hostheader' = $args[0].hostheader
    }

    If (-not $bind_search_splat['hostheader'])
    {
        Get-WebBinding @bind_search_splat -ea stop | Where-Object {$_.BindingInformation.Split(':')[-1] -eq [string]::Empty}
    }
    Else
    {
        Get-WebBinding @bind_search_splat -ea stop
    }
}


# create binding search splat
$binding_parameters = @{
  Name = $name
  Protocol = $protocol
  Port = $port
  IPAddress = $ip
}

# insert host header to search if specified, otherwise it will return * (all bindings matching protocol/ip)
If ($host_header)
{
    $binding_parameters.HostHeader = $host_header
}

# Get bindings matching parameters
Try {
    $current_bindings = Get-SingleWebBinding $binding_parameters
    $binding_info = Create-BindingInfo $current_bindings
    $result.binding = $binding_info
    exit-json -obj $result
}
Catch {
    Fail-Json -obj $result -message "Failed to retrieve bindings with Get-SingleWebBinding - $($_.Exception.Message)"
}