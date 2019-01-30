#!powershell

# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic
#Requires -Module Ansible.ModuleUtils.Legacy
#Requires -Module Ansible.ModuleUtils.FileUtil
#Requires -Module Ansible.ModuleUtils.LinkUtil

function DateTo-Timestamp($start_date, $end_date) {
    if ($start_date -and $end_date) {
        return (New-TimeSpan -Start $start_date -End $end_date).TotalSeconds
    }
}

$spec = @{
    options = @{
        path = @{ type='path'; required=$true; aliases=@( 'dest', 'name' ) }
        get_checksum = @{ type='bool'; default=$true }
        checksum_algorithm = @{ type='str'; default='sha1'; choices=@( 'md5', 'sha1', 'sha256', 'sha384', 'sha512' ) }
        get_md5 = @{ type='bool'; default=$false; removed_in_version='2.9' }
    }
    supports_check_mode = $true
}

$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

$path = $module.Params.path
$get_md5 = $module.Params.get_md5
$get_checksum = $module.Params.checksum
$checksum_algorithm = $module.Params.checksum_algorithm

$module.Result.stat = @{ exists=$false }

$info = Get-AnsibleItem -Path $path -ErrorAction SilentlyContinue
If ($null -ne $info) {
    $epoch_date = Get-Date -Date "01/01/1970"
    $attributes = @()
    foreach ($attribute in ($info.Attributes -split ',')) {
        $attributes += $attribute.Trim()
    }

    # default values that are always set, specific values are set below this
    # but are kept commented for easier readability
    $stat = @{
        exists = $true
        attributes = $info.Attributes.ToString()
        isarchive = ($attributes -contains "Archive")
        isdir = $false
        ishidden = ($attributes -contains "Hidden")
        isjunction = $false
        islnk = $false
        isreadonly = ($attributes -contains "ReadOnly")
        isreg = $false
        isshared = $false
        nlink = 1  # Number of links to the file (hard links), overriden below if islnk
        # lnk_target = islnk or isjunction Target of the symlink. Note that relative paths remain relative
        # lnk_source = islnk os isjunction Target of the symlink normalized for the remote filesystem
        hlnk_targets = @()
        creationtime = (DateTo-Timestamp -start_date $epoch_date -end_date $info.CreationTime)
        lastaccesstime = (DateTo-Timestamp -start_date $epoch_date -end_date $info.LastAccessTime)
        lastwritetime = (DateTo-Timestamp -start_date $epoch_date -end_date $info.LastWriteTime)
        # size = a file and directory - calculated below
        path = $info.FullName
        filename = $info.Name
        # extension = a file
        # owner = set outsite this dict in case it fails
        # sharename = a directory and isshared is True
        # checksum = a file and get_checksum: True
        # md5 = a file and get_md5: True
    }
    try {
        $stat.owner = $info.GetAccessControl().Owner
    } catch {
        # may not have rights, historical behaviour was to just set to $null
        # due to ErrorActionPreference being set to "Continue"
        $stat.owner = $null
    }

    # values that are set according to the type of file
    if ($info.Attributes.HasFlag([System.IO.FileAttributes]::Directory)) {
        $stat.isdir = $true
        $share_info = Get-WmiObject -Class Win32_Share -Filter "Path='$($stat.path -replace '\\', '\\')'"
        if ($share_info -ne $null) {
            $stat.isshared = $true
            $stat.sharename = $share_info.Name
        }

        try {
            $size = 0
            foreach ($file in $info.EnumerateFiles("*", [System.IO.SearchOption]::AllDirectories)) {
                $size += $file.Length
            }
            $stat.size = $size
        } catch {
            $stat.size = 0
        }
    } else {
        $stat.extension = $info.Extension
        $stat.isreg = $true
        $stat.size = $info.Length

        if ($get_md5) {
            try {
                $stat.md5 = Get-FileChecksum -path $path -algorithm "md5"
            } catch {
                $module.FailJson("Failed to get MD5 hash of file, remove get_md5 to ignore this error: $($_.Exception.Message)", $_)
            }
        }
        if ($get_checksum) {
            try {
                $stat.checksum = Get-FileChecksum -path $path -algorithm $checksum_algorithm
            } catch {
                $module.FailJson("Failed to get hash of file, set get_checksum to False to ignore this error: $($_.Exception.Message)", $_)
            }
        }
    }

    # Get symbolic link, junction point, hard link info
    Load-LinkUtils
    try {
        $link_info = Get-Link -link_path $info.FullName
    } catch {
        $module.Warn("Failed to check/get link info for file: $($_.Exception.Message)")
    }
    if ($link_info -ne $null) {
        switch ($link_info.Type) {
            "SymbolicLink" {
                $stat.islnk = $true
                $stat.isreg = $false
                $stat.lnk_target = $link_info.TargetPath
                $stat.lnk_source = $link_info.AbsolutePath
                break
            }
            "JunctionPoint" {
                $stat.isjunction = $true
                $stat.isreg = $false
                $stat.lnk_target = $link_info.TargetPath
                $stat.lnk_source = $link_info.AbsolutePath
                break
            }
            "HardLink" {
                $stat.lnk_type = "hard"
                $stat.nlink = $link_info.HardTargets.Count

                # remove current path from the targets
                $hlnk_targets = $link_info.HardTargets | Where-Object { $_ -ne $stat.path }
                $stat.hlnk_targets = @($hlnk_targets)
                break
            }
        }
    }

    $module.Result.stat = $stat
}

$module.ExitJson()
