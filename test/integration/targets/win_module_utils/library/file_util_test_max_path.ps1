#!powershell

#Requires -Module Ansible.ModuleUtils.Legacy
#Requires -Module Ansible.ModuleUtils.FileUtil

$ErrorActionPreference = "Stop"

$params = Parse-Args $args
$path = Get-AnsibleParam -obj $params -name "path" -type "path" -failifempty $true
$encrypt_tests = Get-AnsibleParam -obj $params -name "encrypt_tests" -type "bool" -default $false

$result = @{
    changed = $false
}
Load-FileUtilFunctions

Function Assert-Equals($actual, $expected) {
    if ($actual -ne $expected) {
        $call_stack = (Get-PSCallStack)[1]
        $error_msg = "AssertionError:`r`nActual: `"$actual`" != Expected: `"$expected`"`r`nLine: $($call_stack.ScriptLineNumber), Method: $($call_stack.Position.Text)"
        Fail-Json -obj $result -message $error_msg
    }
}

Function Assert-ArrayEquals($actual, $expected) {
    $equals = $true
    if ($actual.Count -ne $expected.Count) {
        $equals = $false
    } else {
        for ($i = 0; $i -lt $actual.Count; $i++) {
            if ($actual[$i] -ne $expected[$i]) {
                $equals = $false
                break
            }
        }
    }
    
    if (-not $equals) {
        $call_stack = (Get-PSCallStack)[1]
        $error_msg = "AssertionError:`r`nActual: `"$actual`" != Expected: `"$expected`"`r`nLine: $($call_stack.ScriptLineNumber), Method: $($call_stack.Position.Text)"
        Fail-Json -obj $result -message $error_msg
    }
}

Function Clear-TestDirectory($path) {
    $path = "\\?\$path"
    if ([Ansible.IO.Directory]::Exists($path)) {
        [Ansible.IO.Directory]::Delete($path, $true) > $null
    }
    [Ansible.IO.Directory]::CreateDirectory($path) > $null
}

Function Test-FileClass($root_path) {
    $file_path = "$root_path\file.txt"

    ### FileInfo Tests ###
    # Test Class Attributes when file does not exist
    $file = New-Object -TypeName Ansible.IO.FileInfo -ArgumentList $file_path
    Assert-Equals -actual ([Int32]$file.Attributes) -expected -1
    Assert-Equals -actual $file.CreationTimeUtc.ToFileTimeUtc() -expected 0
    Assert-Equals -actual $file.Directory.FullName -expected $root_path
    Assert-Equals -actual $file.DirectoryName -expected $root_path
    Assert-Equals -actual $file.Exists -expected $false
    Assert-Equals -actual $file.Extension -expected ".txt"
    Assert-Equals -actual $file.FullName -expected $file_path
    Assert-Equals -actual $file.IsReadOnly -expected $true
    Assert-Equals -actual $file.LastAccessTimeUtc.ToFileTimeUtc() -expected 0
    Assert-Equals -actual $file.LastWriteTimeUtc.ToFileTimeUtc() -expected 0
    Assert-Equals -actual $file.Length -expected $null
    Assert-Equals -actual $file.Name -expected "file.txt"
    
    # Test Class Attributes when file exists
    $current_time = (Get-Date).ToFileTImeUtc()
    $fs = $file.Create()
    $fs.Close()
    $file.Refresh()
    Assert-Equals -actual $file.Attributes -expected ([System.IO.FileAttributes]::Archive)
    Assert-Equals -actual ($file.CreationTimeUtc.ToFileTimeUtc() -ge $current_time) -expected $true
    Assert-Equals -actual $file.Directory.FullName -expected $root_path
    Assert-Equals -actual $file.DirectoryName -expected $root_path
    Assert-Equals -actual $file.Exists -expected $true
    Assert-Equals -actual $file.Extension -expected ".txt"
    Assert-Equals -actual $file.FullName -expected $file_path
    Assert-Equals -actual $file.IsReadOnly -expected $false
    Assert-Equals -actual ($file.LastAccessTimeUtc.ToFileTimeUtc() -ge $current_time) -expected $true
    Assert-Equals -actual ($file.LastWriteTimeUtc.ToFileTimeUtc() -ge $current_time) -expected $true
    Assert-Equals -actual $file.Length -expected 0
    Assert-Equals -actual $file.Name -expected "file.txt"

    # Set Properties
    $file.Attributes = $file.Attributes -bor [System.IO.FileAttributes]::Hidden
    $file.Refresh()
    Assert-Equals -actual $file.Attributes -expected ([System.IO.FileAttributes]::Archive -bor [System.IO.FileAttributes]::Hidden)

    $file.IsReadOnly = $true
    $file.Refresh()
    Assert-Equals -actual $file.Attributes.HasFlag([System.IO.FileAttributes]::ReadOnly) -expected $true

    $file.IsReadOnly = $false
    $file.Refresh()
    Assert-Equals -actual $file.Attributes.HasFlag([System.IO.FileAttributes]::ReadOnly) -expected $false
    
    $new_date = (Get-Date -Date "1993-06-11 06:51:32Z")
    $file.CreationTimeUtc = $new_date
    $file.Refresh()
    Assert-Equals -actual $file.CreationTimeUtc -expected $new_date

    $file.LastAccessTimeUtc = $new_date
    $file.Refresh()
    Assert-Equals -actual $file.LastAccessTimeUtc -expected $new_date

    $file.LastWriteTimeUtc = $new_date
    $file.Refresh()
    Assert-Equals -actual $file.LastWriteTimeUtc -expected $new_date

    # Test Functions
    # CreateText() fails if the file is already open
    $failed = $false
    try {
        $sw = $file.CreateText()
        $sw.Close()
    } catch {
        $failed = $true
        Assert-Equals -actual $_.Exception.Message -expected "Exception calling `"CreateText`" with `"0`" argument(s): `"CreateFileW($root_path\file.txt) failed (Access is denied, Win32ErrorCode 5)`""
    }
    Assert-Equals -actual $failed -expected $true

    $file.Delete()
    $file.Refresh()
    Assert-Equals -actual $file.Exists -expected $false
    
    $sw = $file.CreateText()
    try {
        $sw.WriteLine("line1")
        $sw.WriteLine("line2")
    } finally {
        $sw.Close()
    }
    $file.Refresh()

    $sr = $file.OpenText()
    try {
        $file_contents = $sr.ReadToEnd()
    } finally {
        $sr.Close()
    }
    Assert-Equals -actual $file_contents -expected "line1`r`nline2`r`n"

    $copied_file = $file.CopyTo("$root_path\copy.txt")
    Assert-Equals -actual $file.Exists -expected $true
    Assert-Equals -actual ([Ansible.IO.File]::Exists("$root_path\copy.txt")) -expected $true
    $file_hash = Get-AnsibleFileHash -Path $file.FullName
    $copied_file_hash = Get-AnsibleFileHash -Path $copied_file.FullName
    Assert-Equals -actual $file_hash -expected $copied_file_hash

    $failed = $false
    try {
        $file.CopyTo("$root_path\copy.txt")
    } catch {
        Assert-Equals -actual $_.Exception.Message -expected "Exception calling `"CopyTo`" with `"1`" argument(s): `"CopyFileW failed to copy $root_path\file.txt to $root_path\copy.txt (The file exists, Win32ErrorCode 80)`""
        $failed = $true
    }
    Assert-Equals -actual $failed -expected $true

    $sw = $file.AppendText()
    try {
        $sw.WriteLine("line3")
    } finally {
        $sw.Close()
    }
    $copied_file = $file.CopyTo("$root_path\copy.txt", $true)
    Assert-Equals -actual $file.Exists -expected $true
    Assert-Equals -actual ([Ansible.IO.File]::Exists("$root_path\copy.txt")) -expected $true
    $file_hash = Get-AnsibleFileHash -Path $file.FullName
    $copied_file_hash = Get-AnsibleFileHash -Path $copied_file.FullName
    Assert-Equals -actual $file_hash -expected $copied_file_hash

    # also test out the line3 was appended correctly
    $sr = $file.OpenText()
    try {
        $file_contents = $sr.ReadToEnd()
    } finally {
        $sr.Close()
    }
    Assert-Equals -actual $file_contents -expected "line1`r`nline2`r`nline3`r`n"

    # these tests will only work over WinRM when become or CredSSP is used
    if ($encrypt_tests) {
        $file.Encrypt()
        $file.Refresh()
        Assert-Equals $file.Attributes.HasFlag([System.IO.FileAttributes]::Encrypted) -expected $true

        $file.Decrypt()
        $file.Refresh()
        Assert-Equals $file.Attributes.HasFlag([System.IO.FileAttributes]::Encrypted) -expected $false
    }

    $original_hash = Get-AnsibleFileHash -Path $copied_file.FullName
    $copied_file.MoveTo("$root_path\moved.txt")
    Assert-Equals -actual ([Ansible.IO.File]::Exists("$root_path\copy.txt")) -expected $false
    Assert-Equals -actual ([Ansible.IO.File]::Exists("$root_path\moved.txt")) -expected $true
    $moved_hash = Get-AnsibleFileHash -path "$root_path\moved.txt"
    Assert-Equals -actual $moved_hash -expected $original_hash

    $target_file = New-Object -TypeName Ansible.IO.FileInfo -ArgumentList "$root_path\target.txt"
    $backup_file = New-Object -TypeName Ansible.IO.FileInfo -ArgumentList "$root_path\backup.txt"
    $sw = $target_file.CreateText()
    try {
        $sw.WriteLine("original target")
    } finally {
        $sw.Close()
    }
    $original_target_hash = Get-AnsibleFileHash -Path $target_file.FullName
    $original_source_hash = Get-AnsibleFileHash -Path $file.FullName
    $replaced_file = $file.Replace($target_file.FullName, $backup_file.FullName)
    $file.Refresh()
    $target_file.Refresh()
    $backup_file.Refresh()
    $new_target_hash = Get-AnsibleFileHash -Path $replaced_file.FullName
    $backup_hash = Get-AnsibleFileHash -Path $backup_file.FullName
    Assert-Equals -actual $file.Exists -expected $false
    Assert-Equals -actual $replaced_file.FullName -expected $target_file.FullName
    Assert-Equals -actual $replaced_file.Exists -expected $true
    Assert-Equals -actual $backup_file.Exists -expected $true
    Assert-Equals -actual $new_target_hash -expected $original_source_hash
    Assert-Equals -actual $backup_hash -expected $original_target_hash
    $file = $replaced_file

    $fs = $file.OpenRead()
    $failed = $false
    try {
        $fs.WriteByte([byte]0x21)
    } catch {
        $failed = $true
        Assert-Equals -actual $_.Exception.Message -expected "Exception calling `"WriteByte`" with `"1`" argument(s): `"Stream does not support writing.`""
    } finally {
        $fs.Close()
    }
    Assert-Equals -actual $failed -expected $true

    $fs = $file.OpenRead()
    try {
        $file_bytes = New-Object -TypeName Byte[] -ArgumentList $fs.Length
        $bytes_read = $fs.Read($file_bytes, 0, $fs.Length)
    } finally {
        $fs.Close()
    }
    $file_contents = ([System.Text.Encoding]::UTF8).GetString($file_bytes)
    Assert-Equals -actual $file_contents -expected "line1`r`nline2`r`nline3`r`n"

    $fs = $file.OpenWrite()
    try {
        $fs.WriteByte([byte]0x21)
    } finally {
        $fs.Close()
    }
    $fs = $file.OpenRead()
    try {
        $file_bytes = New-Object -TypeName Byte[] -ArgumentList $fs.Length
        $bytes_read = $fs.Read($file_bytes, 0, $fs.Length)
    } finally {
        $fs.Close()
    }
    $file_contents = ([System.Text.Encoding]::UTF8).GetString($file_bytes)
    Assert-Equals -actual $file_contents -expected "!ine1`r`nline2`r`nline3`r`n"

    $fs = $file.Open([System.IO.FileMode]::Create, [System.IO.FileAccess]::Write, [System.IO.FileShare]::ReadWrite)
    try {
        $fs.WriteByte([byte]0x21)
        $fs.Flush()
    } finally {
        $fs.Close()
    }
    $fs = $file.Open([System.IO.FileMode]::Open, [System.IO.FileAccess]::Read)
    try {
        $file_bytes = New-Object -TypeName Byte[] -ArgumentList $fs.Length
        $bytes_read = $fs.Read($file_bytes, 0, $fs.Length)
    } finally {
        $fs.Close()
    }
    $file_contents = ([System.Text.Encoding]::UTF8).GetString($file_bytes)
    Assert-Equals -actual $file_contents -expected "!"

    # open a file with append (CreateFileW doesn't work with append so make sure the stuff around it is fine)
    $fs = $file.Open([System.IO.FileMode]::Append, [System.IO.FileAccess]::Write)
    try {
        $fs.WriteByte([byte]0x21)
        $fs.Flush()
    } finally {
        $fs.Close()
    }
    $fs = $file.Open([System.IO.FileMode]::Open, [System.IO.FileAccess]::Read)
    try {
        $file_bytes = New-Object -TypeName Byte[] -ArgumentList $fs.Length
        $bytes_read = $fs.Read($file_bytes, 0, $fs.Length)
    } finally {
        $fs.Close()
    }
    $file_contents = ([System.Text.Encoding]::UTF8).GetString($file_bytes)
    Assert-Equals -actual $file_contents -expected "!!"

    $current_sid = ([System.Security.Principal.WindowsIdentity]::GetCurrent()).User
    $everyone_sid = New-Object -TypeName System.Security.Principal.SecurityIdentifier -ArgumentList "S-1-1-0"
    
    $acl = New-Object -TypeName System.Security.AccessControl.FileSecurity
    $acl.SetGroup($everyone_sid)
    $acl.SetOwner($current_sid)
    $acl.SetAccessRule((New-Object -TypeName System.Security.AccessControl.FileSystemAccessRule -ArgumentList $everyone_sid, "FullControl", "Allow"))
    $file.SetAccessControl($acl)

    $file.Refresh()
    $acl = $file.GetAccessControl()
    $access_rules = $acl.GetAccessRules($true, $true, [System.Security.Principal.SecurityIdentifier])
    $explicit_access_rules = $access_rules | Where-Object { $_.IsInherited -eq $false }
    $owner = $acl.GetOwner([System.Security.Principal.SecurityIdentifier])
    $group = $acl.GetGroup([System.Security.Principal.SecurityIdentifier])
    Assert-Equals -actual $owner -expected $current_sid
    Assert-Equals -actual $group -expected $everyone_sid
    Assert-Equals -actual $explicit_access_rules.Count -expected 1
    Assert-Equals -actual $explicit_access_rules[0].IdentityReference -expected $everyone_sid
    
    $limited_acl = $file.GetAccessControl([System.Security.AccessControl.AccessControlSections]::Owner)
    $owner = $limited_acl.GetOwner([System.Security.Principal.SecurityIdentifier])
    $group = $limited_acl.GetGroup([System.Security.Principal.SecurityIdentifier])
    Assert-Equals -actual $owner -expected $current_sid
    Assert-Equals -actual $group -expected $null

    ### File Tests ###
    Assert-Equals -actual ([Ansible.IO.File]::Exists($root_path)) -expected $false
    Assert-Equals -actual ([Ansible.IO.File]::Exists($file_path)) -expected $false

    $fs = [Ansible.IO.File]::Create($file_path)
    $fs.Close()
    Assert-Equals -actual ([Ansible.IO.File]::Exists($file_path)) -expected $true

    [Ansible.IO.File]::Delete($file_path)
    Assert-Equals -actual ([Ansible.IO.File]::Exists($file_path)) -expected $false

    $fs = [Ansible.IO.File]::Create($file_path, 4096, [System.IO.FileOptions]::None, $acl)
    $fs.Close()
    $acl = [Ansible.IO.File]::GetAccessControl($file_path)
    $access_rules = $acl.GetAccessRules($true, $true, [System.Security.Principal.SecurityIdentifier])
    $explicit_access_rules = $access_rules | Where-Object { $_.IsInherited -eq $false }
    $owner = $acl.GetOwner([System.Security.Principal.SecurityIdentifier])
    $group = $acl.GetGroup([System.Security.Principal.SecurityIdentifier])
    Assert-Equals -actual $owner -expected $current_sid
    Assert-Equals -actual $group -expected $everyone_sid
    Assert-Equals -actual $explicit_access_rules.Count -expected 1
    Assert-Equals -actual $explicit_access_rules[0].IdentityReference -expected $everyone_sid

    # need to be an admin to set this
    if ([bool](([System.Security.Principal.WindowsIdentity]::GetCurrent()).groups -match "S-1-5-32-544")) {
        $admin_sid = New-Object -TypeName System.Security.Principal.SecurityIdentifier -ArgumentList "S-1-5-32-544"
        $acl.SetOwner($admin_sid)
        [Ansible.IO.File]::SetAccessControl($file_path, $acl)

        $limited_acl = [Ansible.IO.File]::GetAccessControl($file_path, [System.Security.AccessControl.AccessControlSections]::Owner)
        $owner = $limited_acl.GetOwner([System.Security.Principal.SecurityIdentifier])
        $group = $limited_acl.GetGroup([System.Security.Principal.SecurityIdentifier])
        Assert-Equals -actual $owner -expected $admin_sid
        Assert-Equals -actual $group -expected $null
    }

    [Ansible.IO.File]::SetCreationTimeUtc($file_path, $new_date)
    $creation_time = [Ansible.IO.File]::GetCreationTimeUtc($file_path)
    Assert-Equals -actual $creation_time -expected $new_date

    [Ansible.IO.File]::SetLastAccessTimeUtc($file_path, $new_date)
    $lastaccess_time = [Ansible.IO.File]::GetLastAccessTimeUtc($file_path)
    Assert-Equals -actual $lastaccess_time -expected $new_date

    [Ansible.IO.File]::SetLastWriteTimeUtc($file_path, $new_date)
    $lastwrite_time = [Ansible.IO.File]::GetLastWriteTimeUtc($file_path)
    Assert-Equals -actual $lastwrite_time -expected $new_date

    $attributes = [Ansible.IO.File]::GetAttributes($file_path)
    Assert-Equals -actual $attributes -expected ([System.IO.FileAttributes]::Archive)

    [Ansible.IO.File]::SetAttributes($file_path, ($attributes -bor [System.IO.FileAttributes]::Hidden))
    $attributes = [Ansible.IO.File]::GetAttributes($file_path)
    Assert-Equals -actual $attributes -expected ([System.IO.FileAttributes]::Archive -bor [System.IO.FileAttributes]::Hidden)

    if ($encrypt_tests) {
        [Ansible.IO.File]::Encrypt($file_path)
        $attributes = [Ansible.IO.File]::GetAttributes($file_path)
        Assert-Equals -actual $attributes.HasFlag([System.IO.FileAttributes]::Encrypted) -expected $true

        [Ansible.IO.File]::Decrypt($file_path)
        $attributes = [Ansible.IO.File]::GetAttributes($file_path)
        Assert-Equals -actual $attributes.HasFlag([System.IO.FileAttributes]::Encrypted) -expected $false
    }

    [Ansible.IO.File]::AppendAllText($file_path, "line1`r`nline2`r`n")
    $file_contents = [Ansible.IO.File]::ReadAllText($file_path)
    Assert-Equals -actual $file_contents -expected "line1`r`nline2`r`n"

    [Ansible.IO.File]::AppendAllText($file_path, "line3`r`nline4`r`n")
    $file_contents = [Ansible.IO.File]::ReadAllText($file_path)
    Assert-Equals -actual $file_contents -expected "line1`r`nline2`r`nline3`r`nline4`r`n"

    [Ansible.IO.File]::Copy($file_path, "$root_path\copy-file.txt")
    Assert-Equals -actual ([Ansible.IO.File]::Exists($file_path)) -expected $true
    Assert-Equals -actual ([Ansible.IO.File]::Exists("$root_path\copy-file.txt")) -expected $true
    $source_hash = Get-AnsibleFileHash -Path $file_path
    $target_hash = Get-AnsibleFileHash -Path "$root_path\copy-file.txt"
    Assert-Equals -actual $target_hash -expected $source_hash

    [Ansible.IO.File]::Move($file_path, "$root_path\move-file.txt")
    Assert-Equals -actual ([Ansible.IO.File]::Exists($file_path)) -expected $false
    Assert-Equals -actual ([Ansible.IO.File]::Exists("$root_path\move-file.txt")) -expected $true
    $target_hash = Get-AnsibleFileHash -Path "$root_path\move-file.txt"
    Assert-Equals -actual $target_hash -expected $source_hash

    $failed = $false
    try {
        [Ansible.IO.File]::Move("$root_path\copy-file.txt", "$root_path\move-file.txt")
    } catch {
        $failed = $true
        Assert-Equals -actual $_.Exception.Message -expected "Exception calling `"Move`" with `"2`" argument(s): `"MoveFileExW() failed to copy $root_path\copy-file.txt to $root_path\move-file.txt (Cannot create a file when that file already exists, Win32ErrorCode 183)`""
    }
    Assert-Equals -actual $failed -expected $true

    $fs = [Ansible.IO.File]::Create($file_path)
    $fs.Close()
    [Ansible.IO.File]::AppendAllText($file_path, "source text")
    [Ansible.IO.File]::Delete("$root_path\target.txt")
    $fs = [Ansible.IO.File]::Create("$root_path\target.txt")
    $fs.Close()
    [Ansible.IO.File]::AppendAllText("$root_path\target.txt", "target text")

    $source_hash = Get-AnsibleFileHash -Path $file_path
    $target_hash = Get-AnsibleFileHash -Path "$root_path\target.txt"
    [Ansible.IO.File]::Replace($file_path, "$root_path\target.txt", "$root_path\backup.txt")
    Assert-Equals -actual ([Ansible.IO.File]::Exists($file_path)) -expected $false
    Assert-Equals -actual ([Ansible.IO.File]::Exists("$root_path\target.txt")) -expected $true
    Assert-Equals -actual ([Ansible.IO.File]::Exists("$root_path\backup.txt")) -expected $true
    $new_target_hash = Get-AnsibleFileHash -Path "$root_path\target.txt"
    $backup_hash = Get-AnsibleFileHash -Path "$root_path\backup.txt"
    Assert-Equals -actual $new_target_hash -expected $source_hash
    Assert-Equals -actual $backup_hash -expected $target_hash

    $file_bytes = [Ansible.IO.File]::ReadAllBytes("$root_path\target.txt")
    $file_contents = ([System.Text.Encoding]::UTF8).GetString($file_bytes)
    $a = ([System.Text.Encoding]::UTF8).GetBytes("source text")
    Assert-Equals -actual $file_contents.Remove(0, 1) -expected "source text"

    $utf8_bytes = ([System.Text.Encoding]::UTF8).GetBytes("Hello World!")
    $utf16_bytes = ([System.Text.Encoding]::Unicode).GetBytes("Hello World!")
    $fs = [Ansible.IO.File]::OpenWrite("$root_path\utf8.txt")
    try {
        $fs.Write($utf8_bytes, 0, $utf8_bytes.Length)
    } finally {
        $fs.Close()
    }
    $fs = [Ansible.IO.File]::OpenWrite("$root_path\utf16.txt")
    try {
        $fs.Write($utf16_bytes, 0, $utf16_bytes.Length)
    } finally {
        $fs.Close()
    }

    [Ansible.IO.File]::AppendAllText("$root_path\utf8.txt", "`r`nanother line")
    $expected_text = "Hello World!`r`nanother line"
    $expected_bytes = ([System.Text.Encoding]::UTF8).GetBytes($expected_text)
    $file_bytes = [Ansible.IO.File]::ReadAllBytes("$root_path\utf8.txt")
    $file_text = [Ansible.IO.File]::ReadAllText("$root_path\utf8.txt")
    $file_lines = [Ansible.IO.File]::ReadAllLines("$root_path\utf8.txt")
    $file_lines_enumerable = [Ansible.IO.File]::ReadLines("$root_path\utf8.txt")
    Assert-ArrayEquals -actual $file_bytes -expected $expected_bytes
    Assert-Equals -actual $file_text -expected $expected_text
    Assert-Equals -actual $file_lines.Count -expected 2
    Assert-Equals -actual $file_lines[0] -expected "Hello World!"
    Assert-Equals -actual $file_lines[1] -expected "another line"
    $is_first = $true
    foreach ($line in $file_lines_enumerable) {
        if ($is_first) {
            Assert-Equals -actual $line -expected "Hello World!"
        } else {
            Assert-Equals -actual $line -expected "another line"
        }
        $is_first = $false
    }


    [Ansible.IO.File]::AppendAllText("$root_path\utf16.txt", "`r`nanother line", [System.Text.Encoding]::Unicode)
    $expected_text = "Hello World!`r`nanother line"
    $expected_bytes = ([System.Text.Encoding]::Unicode).GetBytes($expected_text)
    $file_bytes = [Ansible.IO.File]::ReadAllBytes("$root_path\utf16.txt")
    $file_text = [Ansible.IO.File]::ReadAllText("$root_path\utf16.txt", [System.Text.Encoding]::Unicode)
    $file_lines = [Ansible.IO.File]::ReadAllLines("$root_path\utf16.txt", [System.Text.Encoding]::Unicode)
    $file_lines_enumerable = [Ansible.IO.File]::ReadLines("$root_path\utf16.txt", [System.Text.Encoding]::Unicode)
    Assert-ArrayEquals -actual $file_bytes -expected $expected_bytes
    Assert-Equals -actual $file_text -expected $expected_text
    Assert-Equals -actual $file_lines.Count -expected 2
    Assert-Equals -actual $file_lines[0] -expected "Hello World!"
    Assert-Equals -actual $file_lines[1] -expected "another line"
    $is_first = $true
    foreach ($line in $file_lines_enumerable) {
        if ($is_first) {
            Assert-Equals -actual $line -expected "Hello World!"
        } else {
            Assert-Equals -actual $line -expected "another line"
        }
        $is_first = $false
    }

    [Ansible.IO.File]::WriteAllLines("$root_path\utf8.txt", [string[]]@("line 1", "line 2"))
    $expected_bytes = [byte[]](([System.Text.Encoding]::UTF8).GetPreamble() + ([System.Text.Encoding]::UTF8).GetBytes("line 1`r`nline 2`r`n"))
    $file_bytes = [Ansible.IO.File]::ReadAllBytes("$root_path\utf8.txt")
    Assert-ArrayEquals -actual $file_bytes -expected $expected_bytes

    [Ansible.IO.File]::WriteAllLines("$root_path\utf16.txt", [string[]]@("line 1", "line 2"), [System.Text.Encoding]::Unicode)
    $expected_bytes = [byte[]](([System.Text.Encoding]::Unicode).GetPreamble() + ([System.Text.Encoding]::Unicode).GetBytes("line 1`r`nline 2`r`n"))
    $file_bytes = [Ansible.IO.File]::ReadAllBytes("$root_path\utf16.txt")
    Assert-ArrayEquals -actual $file_bytes -expected $expected_bytes

    [Ansible.IO.File]::WriteAllText("$root_path\utf8.txt", "another line 1`r`nanother line 2`r`n")
    $expected_bytes = [byte[]](([System.Text.Encoding]::UTF8).GetPreamble() + ([System.Text.Encoding]::UTF8).GetBytes("another line 1`r`nanother line 2`r`n"))
    $file_bytes = [Ansible.IO.File]::ReadAllBytes("$root_path\utf8.txt")
    Assert-ArrayEquals -actual $file_bytes -expected $expected_bytes

    [Ansible.IO.File]::WriteAllText("$root_path\utf16.txt", "another line 1`r`nanother line 2`r`n", [System.Text.Encoding]::Unicode)
    $expected_bytes = [byte[]](([System.Text.Encoding]::Unicode).GetPreamble() + ([System.Text.Encoding]::Unicode).GetBytes("another line 1`r`nanother line 2`r`n"))
    $file_bytes = [Ansible.IO.File]::ReadAllBytes("$root_path\utf16.txt")
    Assert-ArrayEquals -actual $file_bytes -expected $expected_bytes

    [Ansible.IO.File]::WriteAllBytes("$root_path\utf8.txt", [byte[]]@(0x21, 0x21))
    $file_contents = [Ansible.IO.File]::ReadAllText("$root_path\utf8.txt")
    Assert-Equals -actual $file_contents -expected "!!"

    $sw = [Ansible.IO.File]::AppendText("$root_path\utf8.txt")
    try {
        $sw.WriteLine("!!")
    } finally {
        $sw.Close()
    }
    $file_contents = [Ansible.IO.File]::ReadAllText("$root_path\utf8.txt")
    Assert-Equals -actual $file_contents -expected "!!!!`r`n"

    $sw = [Ansible.IO.File]::CreateText("$root_path\utf8.txt")
    try {
        $sw.WriteLine("!!")
    } finally {
        $sw.Close()
    }
    $file_contents = [Ansible.IO.File]::ReadAllText("$root_path\utf8.txt")
    Assert-Equals -actual $file_contents -expected "!!`r`n"

    $sr = [Ansible.IO.File]::OpenText("$root_path\utf8.txt")
    try {
        $file_contents = $sr.ReadToEnd()
    } finally {
        $sr.Close()
    }
    Assert-Equals -actual $file_contents -expected "!!`r`n"

    $fs = [Ansible.IO.File]::OpenRead("$root_path\utf8.txt")
    try {
        Assert-Equals -actual $fs.CanRead -expected $true
        Assert-Equals -actual $fs.CanWrite -expected $false
        $file_bytes = New-Object -TypeName Byte[] -ArgumentList $fs.Length
        $bytes_read = $fs.Read($file_bytes, 0, $fs.Length)
    } finally {
        $fs.Close()
    }
    Assert-ArrayEquals -actual $file_bytes -expected ([byte[]]@(33, 33, 13, 10))

    $fs = [Ansible.IO.File]::OpenWrite("$root_path\utf8.txt")
    try {
        Assert-Equals -actual $fs.CanRead -expected $false
        Assert-Equals -actual $fs.CanWrite -expected $true
        $fs.WriteByte([byte]32)
    } finally {
        $fs.Close()
    }
    $file_bytes = [Ansible.IO.File]::ReadAllBytes("$root_path\utf8.txt")
    Assert-ArrayEquals -actual $file_bytes -expected ([byte[]]@(32, 33, 13, 10))

    $fs = [Ansible.IO.File]::Open("$root_path\utf8.txt", [System.IO.FileMode]::Create, [System.IO.FileAccess]::Write, [System.IO.FileShare]::ReadWrite)
    try {
        Assert-Equals -actual $fs.CanRead -expected $false
        Assert-Equals -actual $fs.CanWrite -expected $true
        $fs.WriteByte([byte]33)
        $fs.Flush()
    } finally {
        $fs.Close()
    }
    $fs = [Ansible.IO.File]::Open("$root_path\utf8.txt", [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read)
    try {
        Assert-Equals -actual $fs.CanRead -expected $true
        Assert-Equals -actual $fs.CanWrite -expected $false
        $file_bytes = New-Object -TypeName Byte[] -ArgumentList $fs.Length
        $bytes_read = $fs.Read($file_bytes, 0, $fs.Length)
    } finally {
        $fs.Close()
    }
    Assert-ArrayEquals -actual $file_bytes -expected ([byte[]]@(33))

    # open a file with append (CreateFileW doesn't work with append so make sure the stuff around it is fine)
    $fs = [Ansible.IO.File]::Open("$root_path\utf8.txt", [System.IO.FileMode]::Append, [System.IO.FileAccess]::ReadWrite)
    try {
        Assert-Equals -actual $fs.CanRead -expected $true
        Assert-Equals -actual $fs.CanWrite -expected $true
        $fs.WriteByte([byte]32)
        $fs.Flush()
    } finally {
        $fs.Close()
    }
    $file_bytes = [Ansible.IO.File]::ReadAllBytes("$root_path\utf8.txt")
    Assert-ArrayEquals -actual $file_bytes -expected ([byte[]]@(33, 32))
}
Function Test-DirectoryClass($root_path) {
    $directory_path = "$root_path\dir"

    ### DirectoryInfo Tests ###
    $dir = New-Object -TypeName Ansible.IO.DirectoryInfo -ArgumentList $directory_path

    # Test class attributes when it doesn't exist
    Assert-Equals -actual $dir.Exists -expected $false
    Assert-Equals -actual $dir.Name -expected "dir"
    Assert-Equals -actual $dir.Parent.ToString() -expected $root_path
    if ($root_path.StartsWith("\\?\")) {
        Assert-Equals -actual $dir.Root.ToString() -expected "\\?\C:\"
    } else {
        Assert-Equals -actual $dir.Root.ToString() -expected "C:\"
    }
    Assert-Equals -actual ([Int32]$dir.Attributes) -expected -1
    Assert-Equals -actual $dir.CreationTimeUtc.ToFileTimeUtc() -expected 0
    Assert-Equals -actual $dir.Extension -expected ""
    Assert-Equals -actual $dir.FullName -expected $directory_path
    Assert-Equals -actual $dir.LastAccessTimeUtc.ToFileTimeUtc() -expected 0
    Assert-Equals -actual $dir.LastWriteTimeUtc.ToFileTimeUtc() -expected 0

    # create directory
    $current_time = (Get-Date).ToFileTimeUtc()
    $dir.Create()
    $dir.Refresh() # resets the properties of the class

    # Test class attributes when it does exist
    Assert-Equals -actual $dir.Exists -expected $true
    Assert-Equals -actual $dir.Name -expected "dir"
    Assert-Equals -actual $dir.Parent.ToString() -expected $root_path 
    if ($root_path.StartsWith("\\?\")) {
        Assert-Equals -actual $dir.Root.ToString() -expected "\\?\C:\"
    } else {
        Assert-Equals -actual $dir.Root.ToString() -expected "C:\"
    }
    Assert-Equals -actual $dir.Attributes -expected ([System.IO.FileAttributes]::Directory)
    Assert-Equals -actual ($dir.CreationTimeUtc.ToFileTimeUtc() -ge $current_time) -expected $true
    Assert-Equals -actual $dir.Extension -expected ""
    Assert-Equals -actual $dir.FullName -expected $directory_path
    Assert-Equals -actual ($dir.LastAccessTimeUtc.ToFileTimeUtc() -ge $current_time) -expected $true
    Assert-Equals -actual ($dir.LastWriteTimeUtc.ToFileTimeUtc() -ge $current_time) -expected $true

    # set properties
    $dir.Attributes = $dir.Attributes -bor [System.IO.FileAttributes]::Archive -bor [System.IO.FileAttributes]::Hidden
    $dir.Refresh()
    Assert-Equals -actual $dir.Attributes -expected ([System.IO.FileAttributes]::Directory -bor [System.IO.FileAttributes]::Archive -bor [System.IO.FileAttributes]::Hidden)

    $new_date = (Get-Date -Date "1993-06-11 06:51:32Z")
    $dir.CreationTimeUtc = $new_date
    $dir.Refresh()
    Assert-Equals -actual $dir.CreationTimeUtc.ToFileTimeUtc() -expected $new_date.ToFileTimeUtc()
    $dir.LastAccessTimeUtc = $new_date
    $dir.Refresh()
    Assert-Equals -actual $dir.LastAccessTimeUtc.ToFileTimeUtc() -expected $new_date.ToFileTimeUtc()
    $dir.LastWriteTimeUtc = $new_date
    $dir.Refresh()
    Assert-Equals -actual $dir.LastWriteTimeUtc.ToFileTimeUtc() -expected $new_date.ToFileTimeUtc()

    # test DirectoryInfo methods
    # create tests
    $subdir = $dir.CreateSubDirectory("subdir")
    Assert-Equals -actual ([Ansible.IO.Directory]::Exists("$directory_path\subdir")) -expected $true

    # enumerate tests
    $subdir1 = $dir.CreateSubDirectory("subdir-1")
    $subdir2 = $dir.CreateSubDirectory("subdir-2")
    $subdir3 = $subdir1.CreateSubDirectory("subdir3")
    $file = [Ansible.IO.File]::CreateText("$directory_path\file.txt")
    try {
        $file.WriteLine("abc")
    } finally {
        $file.Dispose()
    }
    $file = [Ansible.IO.File]::CreateText("$directory_path\anotherfile.txt")
    try {
        $file.WriteLine("abc")
    } finally {
        $file.Dispose()
    }
    $file = [Ansible.IO.File]::CreateText("$directory_path\subdir-1\file-1.txt")
    try {
        $file.WriteLine("abc")
    } finally {
        $file.Dispose()
    }
    $file = [Ansible.IO.File]::CreateText("$directory_path\subdir-2\file-2.txt")
    try {
        $file.WriteLine("abc")
    } finally {
        $file.Dispose()
    }
    $file = [Ansible.IO.File]::CreateText("$directory_path\subdir-1\subdir3\file-3.txt")
    try {
        $file.WriteLine("abc")
    } finally {
        $file.Dispose()
    }

    $dir_dirs = $dir.EnumerateDirectories()
    foreach ($dir_name in $dir_dirs) {
        Assert-Equals -actual $dir_name.GetType().FullName -expected "Ansible.IO.DirectoryInfo"
        Assert-Equals -actual ($dir_name.Name -in (
            "subdir",
            "subdir-1",
            "subdir-2")) -expected $true
    }
    $dir_dirs = $dir.EnumerateDirectories("subdir-?")
    foreach ($dir_name in $dir_dirs) {
        Assert-Equals -actual $dir_name.GetType().FullName -expected "Ansible.IO.DirectoryInfo"
        Assert-Equals -actual ($dir_name.Name -in (
            "subdir-1",
            "subdir-2")) -expected $true
    }
    $dir_dirs = $dir.EnumerateDirectories("*", [System.IO.SearchOption]::AllDirectories)
    foreach ($dir_name in $dir_dirs) {
        Assert-Equals -actual $dir_name.GetType().FullName -expected "Ansible.IO.DirectoryInfo"
        Assert-Equals -actual ($dir_name.Name -in (
            "subdir",
            "subdir-1",
            "subdir-2",
            "subdir3")) -expected $true
    }

    $dir_dirs = $dir.GetDirectories()
    foreach ($dir_name in $dir_dirs) {
        Assert-Equals -actual $dir_name.GetType().FullName -expected "Ansible.IO.DirectoryInfo"
        Assert-Equals -actual ($dir_name.Name -in (
            "subdir",
            "subdir-1",
            "subdir-2")) -expected $true
    }
    $dir_dirs = $dir.GetDirectories("subdir-?")
    foreach ($dir_name in $dir_dirs) {
        Assert-Equals -actual $dir_name.GetType().FullName -expected "Ansible.IO.DirectoryInfo"
        Assert-Equals -actual ($dir_name.Name -in (
            "subdir-1",
            "subdir-2")) -expected $true
    }
    $dir_dirs = $dir.GetDirectories("*", [System.IO.SearchOption]::AllDirectories)
    foreach ($dir_name in $dir_dirs) {
        Assert-Equals -actual $dir_name.GetType().FullName -expected "Ansible.IO.DirectoryInfo"
        Assert-Equals -actual ($dir_name.Name -in (
            "subdir",
            "subdir-1",
            "subdir-2",
            "subdir3")) -expected $true
    }

    $dir_files = $dir.EnumerateFiles()
    foreach ($dir_file in $dir_files) {
        Assert-Equals -actual $dir_file.GetType().FullName -expected "Ansible.IO.FileInfo"
        Assert-Equals -actual ($dir_file.Name -in (
            "file.txt",
            "anotherfile.txt")) -expected $true
    }
    $dir_files = $dir.EnumerateFiles("anotherfile*")
    foreach ($dir_file in $dir_files) {
        Assert-Equals -actual $dir_file.GetType().FullName -expected "Ansible.IO.FileInfo"
        Assert-Equals -actual ($dir_file.Name -in ("anotherfile.txt")) -expected $true
    }
    $dir_files = $dir.EnumerateFiles("*", [System.IO.SearchOption]::AllDirectories)
    foreach ($dir_file in $dir_files) {
        Assert-Equals -actual $dir_file.GetType().FullName -expected "Ansible.IO.FileInfo"
        Assert-Equals -actual ($dir_file.Name -in (
            "file.txt",
            "anotherfile.txt",
            "file-1.txt",
            "file-2.txt",
            "file-3.txt")) -expected $true
    }

    $dir_files = $dir.GetFiles()
    foreach ($dir_file in $dir_files) {
        Assert-Equals -actual $dir_file.GetType().FullName -expected "Ansible.IO.FileInfo"
        Assert-Equals -actual ($dir_file.Name -in (
            "file.txt",
            "anotherfile.txt")) -expected $true
    }
    $dir_files = $dir.GetFiles("anotherfile*")
    foreach ($dir_file in $dir_files) {
        Assert-Equals -actual $dir_file.GetType().FullName -expected "Ansible.IO.FileInfo"
        Assert-Equals -actual ($dir_file.Name -in ("anotherfile.txt")) -expected $true
    }
    $dir_files = $dir.GetFiles("*", [System.IO.SearchOption]::AllDirectories)
    foreach ($dir_file in $dir_files) {
        Assert-Equals -actual $dir_file.GetType().FullName -expected "Ansible.IO.FileInfo"
        Assert-Equals -actual ($dir_file.Name -in (
            "file.txt",
            "anotherfile.txt",
            "file-1.txt",
            "file-2.txt",
            "file-3.txt")) -expected $true
    }

    $dir_entries = $dir.EnumerateFileSystemInfos()
    foreach ($dir_entry in $dir_entries) {
        Assert-Equals -actual ($dir_entry.GetType().FullName -in @("Ansible.IO.FileInfo", "Ansible.IO.DirectoryInfo")) -expected $true
        Assert-Equals -actual ($dir_entry.Name -in (
            "file.txt",
            "anotherfile.txt",
            "subdir",
            "subdir-1",
            "subdir-2")) -expected $true
    }
    $dir_entries = $dir.EnumerateFileSystemInfos("anotherfile*")
    foreach ($dir_entry in $dir_entries) {
        Assert-Equals -actual ($dir_entry.GetType().FullName -in @("Ansible.IO.FileInfo", "Ansible.IO.DirectoryInfo")) -expected $true
        Assert-Equals -actual ($dir_entry.Name -in ("anotherfile.txt")) -expected $true
    }
    $dir_entries = $dir.EnumerateFileSystemInfos("*", [System.IO.SearchOption]::AllDirectories)
    foreach ($dir_entry in $dir_entries) {
        Assert-Equals -actual ($dir_entry.GetType().FullName -in @("Ansible.IO.FileInfo", "Ansible.IO.DirectoryInfo")) -expected $true
        Assert-Equals -actual ($dir_entry.Name -in (
            "file.txt",
            "anotherfile.txt",
            "file-1.txt",
            "file-2.txt",
            "file-3.txt",
            "subdir",
            "subdir-1",
            "subdir-2",
            "subdir3")) -expected $true
    }

    $dir_entries = $dir.GetFileSystemInfos()
    foreach ($dir_entry in $dir_entries) {
        Assert-Equals -actual ($dir_entry.GetType().FullName -in @("Ansible.IO.FileInfo", "Ansible.IO.DirectoryInfo")) -expected $true
        Assert-Equals -actual ($dir_entry.Name -in (
            "file.txt",
            "anotherfile.txt",
            "subdir",
            "subdir-1",
            "subdir-2")) -expected $true
    }
    $dir_entries = $dir.GetFileSystemInfos("anotherfile*")
    foreach ($dir_entry in $dir_entries) {
        Assert-Equals -actual ($dir_entry.GetType().FullName -in @("Ansible.IO.FileInfo", "Ansible.IO.DirectoryInfo")) -expected $true
        Assert-Equals -actual ($dir_entry.Name -in ("anotherfile.txt")) -expected $true
    }
    $dir_entries = $dir.GetFileSystemInfos("*", [System.IO.SearchOption]::AllDirectories)
    foreach ($dir_entry in $dir_entries) {
        Assert-Equals -actual ($dir_entry.GetType().FullName -in @("Ansible.IO.FileInfo", "Ansible.IO.DirectoryInfo")) -expected $true
        Assert-Equals -actual ($dir_entry.Name -in (
            "file.txt",
            "anotherfile.txt",
            "file-1.txt",
            "file-2.txt",
            "file-3.txt",
            "subdir",
            "subdir-1",
            "subdir-2",
            "subdir3")) -expected $true
    }
    
    # move tests
    $subdir2.MoveTo("$directory_path\subdir-move")
    Assert-Equals -actual ([Ansible.IO.Directory]::Exists("$directory_path\subdir-move")) -expected $true
    Assert-Equals -actual ([Ansible.IO.File]::Exists("$directory_path\subdir-move\file-2.txt")) -expected $true

    # delete tests
    $failed = $false
    try {
        # fail to delete a directory that has contents
        $subdir1.Delete()
    } catch {
        $failed = $true
        Assert-Equals -actual $_.Exception.Message -expected "Exception calling `"Delete`" with `"0`" argument(s): `"RemoveDirectoryW($($subdir1.FullName)) failed (The directory is not empty, Win32ErrorCode 145)`""
    }
    Assert-Equals -actual $failed -expected $true
    $subdir1.Delete($true)
    Assert-Equals -actual ([Ansible.IO.Directory]::Exists("$directory_path\subdir-1")) -expected $false
    $subdir = $dir.CreateSubDirectory("subdir")
    $subdir.Delete()
    Assert-Equals -actual ([Ansible.IO.Directory]::Exists("$directory_path\subdir")) -expected $false

    # ACL tests
    $current_sid = ([System.Security.Principal.WindowsIdentity]::GetCurrent()).User
    $everyone_sid = New-Object -TypeName System.Security.Principal.SecurityIdentifier -ArgumentList "S-1-1-0"

    $dir_sec = New-Object -TypeName System.Security.AccessControl.DirectorySecurity
    $read_rule = New-Object -TypeName System.Security.AccessControl.FileSystemAccessRule -ArgumentList $everyone_sid, "FullControl", "Allow"
    $dir_sec.SetAccessRule($read_rule)
    $dir_sec.SetOwner($current_sid)
    $dir_sec.SetGroup($everyone_sid)
    $acl_dir = $dir.CreateSubDirectory("acl-dir", $dir_sec)

    $actual_acl = $acl_dir.GetAccessControl()
    $access_rules = $actual_acl.GetAccessRules($true, $true, [System.Security.Principal.SecurityIdentifier])

    $acl_owner = $actual_acl.GetOwner([System.Security.Principal.SecurityIdentifier])
    $acl_group = $actual_acl.GetGroup([System.Security.Principal.SecurityIdentifier])
    Assert-Equals -actual $acl_owner -expected $current_sid
    Assert-Equals -actual $acl_group -expected $everyone_sid

    # only admins can set audit rules, we test for failure if not running as admin
    $audit_rule = New-Object -TypeName System.Security.AccessControl.FileSystemAuditRule -ArgumentList $everyone_sid, "Read", "Success"
    $dir_sec = $acl_dir.GetAccessControl()
    $dir_sec.SetAuditRule($audit_rule)
    if ([bool](([System.Security.Principal.WindowsIdentity]::GetCurrent()).groups -match "S-1-5-32-544")) {
        $acl_dir.SetAccessControl($dir_sec)
        $actual_acl = $acl_dir.GetAccessControl([System.Security.AccessControl.AccessControlSections]::All)
        $audit_rules = $actual_acl.GetAuditRules($true, $true, [System.Security.Principal.SecurityIdentifier])
        Assert-Equals -actual $audit_rules.Count -expected 1
        Assert-Equals -actual $audit_rules[0].FileSystemRights.ToString() -expected "Read"
        Assert-Equals -actual $audit_rules[0].AuditFlags.ToString() -expected "Success"
        Assert-Equals -actual $audit_rules[0].IsInherited -expected $false
        Assert-Equals -actual $audit_rules[0].IdentityReference -expected $everyone_sid
    } else {
        $failed = $false
        try {
            $acl_dir.SetAccessControl($dir_sec)
        } catch {
            $failed = $true
            Assert-Equals -actual $_.Exception.Message -expected "Exception calling `"SetAccessControl`" with `"1`" argument(s): `"SetNamedSecurityInfoW($($acl_dir.FullName)) failed (A required privilege is not held by the client, Win32ErrorCode 1314)`""
        }
        Assert-Equals -actual $failed -expected $true
    }

    # clear for the Ansible.IO.Directory tests
    [Ansible.IO.Directory]::Delete($directory_path, $true)

    ### Directory Tests ###
    $dir = [Ansible.IO.Directory]::CreateDirectory($directory_path)
    Assert-Equals -actual ($dir -is [Ansible.IO.DirectoryInfo]) -expected $true
    Assert-Equals -actual ([Ansible.IO.Directory]::Exists($directory_path)) -expected $true

    # ACL Tests
    $acl = New-Object -TypeName System.Security.AccessControl.DirectorySecurity
    $read_rule = New-Object -TypeName System.Security.AccessControl.FileSystemAccessRule -ArgumentList $everyone_sid, "FullControl", "Allow"
    $acl.SetAccessRule($read_rule)
    $acl.SetOwner($current_sid)
    $acl.SetGroup($everyone_sid)
    $acl_dir = [Ansible.IO.Directory]::CreateDirectory("$directory_path\acl-dir", $acl)
    Assert-Equals -actual ($acl_dir -is [Ansible.IO.DirectoryInfo]) -expected $true

    $acl = [Ansible.IO.Directory]::GetAccessControl("$directory_path\acl-dir")
    $access_rules = $acl.GetAccessRules($true, $true, [System.Security.Principal.SecurityIdentifier])
    $owner = $acl.GetOwner([System.Security.Principal.SecurityIdentifier])
    $group = $acl.GetGroup([System.Security.Principal.SecurityIdentifier])
    Assert-Equals -actual $access_rules.Count -expected 1
    Assert-Equals -actual $access_rules[0].IdentityReference -expected $everyone_sid
    Assert-Equals -actual $access_rules[0].IsInherited -expected $false
    Assert-Equals -actual $owner -expected $current_sid
    Assert-Equals -actual $group -expected $everyone_sid

    # only admins can set this
    if ([bool](([System.Security.Principal.WindowsIdentity]::GetCurrent()).groups -match "S-1-5-32-544")) {
        $acl = [Ansible.IO.Directory]::GetAccessControl("$directory_path\acl-dir")
        $admin_sid = New-Object -TypeName System.Security.Principal.SecurityIdentifier -ArgumentList "S-1-5-32-544"
        $acl.SetOwner($admin_sid)
        [Ansible.IO.Directory]::SetAccessControl("$directory_path\acl-dir", $acl)

        $acl_owner = [Ansible.IO.Directory]::GetAccessControl("$directory_path\acl-dir", [System.Security.AccessControl.AccessControlSections]::Owner)
        $owner = $acl_owner.GetOwner([System.Security.Principal.SecurityIdentifier])
        $group = $acl_owner.GetGroup([System.Security.Principal.SecurityIdentifier])
        Assert-Equals -actual $owner -expected $admin_sid
        Assert-Equals -actual $group -expected $null
    }

    [Ansible.IO.Directory]::CreateDirectory("$directory_path\subdir-1") > $null
    [Ansible.IO.Directory]::CreateDirectory("$directory_path\subdir-1\subdir-3") > $null
    [Ansible.IO.Directory]::CreateDirectory("$directory_path\subdir-2") > $null
    $file = [Ansible.IO.File]::CreateText("$directory_path\file.txt")
    try {
        $file.WriteLine("abc")
    } finally {
        $file.Dispose()
    }
    $file = [Ansible.IO.File]::CreateText("$directory_path\anotherfile.txt")
    try {
        $file.WriteLine("abc")
    } finally {
        $file.Dispose()
    }
    $file = [Ansible.IO.File]::CreateText("$directory_path\subdir-1\file-1.txt")
    try {
        $file.WriteLine("abc")
    } finally {
        $file.Dispose()
    }
    $file = [Ansible.IO.File]::CreateText("$directory_path\subdir-1\subdir-3\file-3.txt")
    try {
        $file.WriteLine("abc")
    } finally {
        $file.Dispose()
    }
    $file = [Ansible.IO.File]::CreateText("$directory_path\subdir-2\file-2.txt")
    try {
        $file.WriteLine("abc")
    } finally {
        $file.Dispose()
    }

    $dir_dirs = [Ansible.IO.Directory]::EnumerateDirectories($directory_path)
    foreach ($dir_name in $dir_dirs) {
        Assert-Equals -actual $dir_name.GetType().FullName -expected "System.String"
        Assert-Equals -actual ($dir_name -in (
            "$directory_path\subdir-1",
            "$directory_path\subdir-2",
            "$directory_path\acl-dir")) -expected $true
    }
    $dir_dirs = [Ansible.IO.Directory]::EnumerateDirectories($directory_path, "acl-*")
    foreach ($dir_name in $dir_dirs) {
        Assert-Equals -actual $dir_name.GetType().FullName -expected "System.String"
        Assert-Equals -actual ($dir_name -in ("$directory_path\acl-dir")) -expected $true
    }
    $dir_dirs = [Ansible.IO.Directory]::EnumerateDirectories($directory_path, "*", [System.IO.SearchOption]::AllDirectories)
    foreach ($dir_name in $dir_dirs) {
        Assert-Equals -actual $dir_name.GetType().FullName -expected "System.String"
        Assert-Equals -actual ($dir_name -in (
            "$directory_path\subdir-1",
            "$directory_path\subdir-1\subdir-3",
            "$directory_path\subdir-2",
            "$directory_path\acl-dir")) -expected $true
    }

    $dir_dirs = [Ansible.IO.Directory]::GetDirectories($directory_path)
    Assert-Equals -actual ($dir_dirs.Count) -expected 3
    foreach ($dir_name in $dir_dirs) {
        Assert-Equals -actual $dir_name.GetType().FullName -expected "System.String"
        Assert-Equals -actual ($dir_name -in (
            "$directory_path\subdir-1",
            "$directory_path\subdir-2",
            "$directory_path\acl-dir")) -expected $true
    }
    $dir_dirs = [Ansible.IO.Directory]::GetDirectories($directory_path, "acl-*")
    Assert-Equals -actual ($dir_dirs.Count) -expected 1
    foreach ($dir_name in $dir_dirs) {
        Assert-Equals -actual $dir_name.GetType().FullName -expected "System.String"
        Assert-Equals -actual ($dir_name -in ("$directory_path\acl-dir")) -expected $true
    }
    $dir_dirs = [Ansible.IO.Directory]::GetDirectories($directory_path, "*", [System.IO.SearchOption]::AllDirectories)
    Assert-Equals -actual ($dir_dirs.Count) -expected 4
    foreach ($dir_name in $dir_dirs) {
        Assert-Equals -actual $dir_name.GetType().FullName -expected "System.String"
        Assert-Equals -actual ($dir_name -in (
            "$directory_path\subdir-1",
            "$directory_path\subdir-1\subdir-3",
            "$directory_path\subdir-2",
            "$directory_path\acl-dir")) -expected $true
    }

    $dir_files = [Ansible.IO.Directory]::EnumerateFiles($directory_path)
    foreach ($dir_file in $dir_files) {
        Assert-Equals -actual $dir_file.GetType().FullName -expected "System.String"
        Assert-Equals -actual ($dir_file -in (
            "$directory_path\file.txt",
            "$directory_path\anotherfile.txt")) -expected $true
    }
    $dir_files = [Ansible.IO.Directory]::EnumerateFiles($directory_path, "another*")
    foreach ($dir_file in $dir_files) {
        Assert-Equals -actual $dir_file.GetType().FullName -expected "System.String"
        Assert-Equals -actual ($dir_file -in ("$directory_path\anotherfile.txt")) -expected $true
    }
    $dir_files = [Ansible.IO.Directory]::EnumerateFiles($directory_path, "*", [System.IO.SearchOption]::AllDirectories)
    foreach ($dir_file in $dir_files) {
        Assert-Equals -actual $dir_file.GetType().FullName -expected "System.String"
        Assert-Equals -actual ($dir_file -in (
            "$directory_path\file.txt",
            "$directory_path\anotherfile.txt",
            "$directory_path\subdir-1\file-1.txt",
            "$directory_path\subdir-1\subdir-3\file-3.txt",
            "$directory_path\subdir-2\file-2.txt")) -expected $true
    }

    $dir_files = [Ansible.IO.Directory]::GetFiles($directory_path)
    Assert-Equals -actual ($dir_files.Count) -expected 2
    foreach ($dir_file in $dir_files) {
        Assert-Equals -actual $dir_file.GetType().FullName -expected "System.String"
        Assert-Equals -actual ($dir_file -in (
            "$directory_path\file.txt",
            "$directory_path\anotherfile.txt")) -expected $true
    }
    $dir_files = [Ansible.IO.Directory]::GetFiles($directory_path, "another*")
    Assert-Equals -actual ($dir_files.Count) -expected 1
    foreach ($dir_file in $dir_files) {
        Assert-Equals -actual $dir_file.GetType().FullName -expected "System.String"
        Assert-Equals -actual ($dir_file -in ("$directory_path\anotherfile.txt")) -expected $true
    }
    $dir_files = [Ansible.IO.Directory]::GetFiles($directory_path, "*", [System.IO.SearchOption]::AllDirectories)
    Assert-Equals -actual ($dir_files.Count) -expected 5
    foreach ($dir_file in $dir_files) {
        Assert-Equals -actual $dir_file.GetType().FullName -expected "System.String"
        Assert-Equals -actual ($dir_file -in (
            "$directory_path\file.txt",
            "$directory_path\anotherfile.txt",
            "$directory_path\subdir-1\file-1.txt",
            "$directory_path\subdir-1\subdir-3\file-3.txt",
            "$directory_path\subdir-2\file-2.txt")) -expected $true
    }

    $dir_entries = [Ansible.IO.Directory]::EnumerateFileSystemEntries($directory_path)
    foreach ($dir_entry in $dir_entries) {
        Assert-Equals -actual $dir_entry.GetType().FullName -expected "System.String"
        Assert-Equals -actual ($dir_entry -in (
            "$directory_path\subdir-1",
            "$directory_path\subdir-2",
            "$directory_path\acl-dir",
            "$directory_path\file.txt",
            "$directory_path\anotherfile.txt")) -expected $true
    }
    $dir_entries = [Ansible.IO.Directory]::EnumerateFileSystemEntries($directory_path, "another*")
    foreach ($dir_entry in $dir_entries) {
        Assert-Equals -actual $dir_entry.GetType().FullName -expected "System.String"
        Assert-Equals -actual ($dir_entry -in ("$directory_path\anotherfile.txt")) -expected $true
    }
    $dir_entries = [Ansible.IO.Directory]::EnumerateFileSystemEntries($directory_path, "*", [System.IO.SearchOption]::AllDirectories)
    foreach ($dir_entry in $dir_entries) {
        Assert-Equals -actual $dir_entry.GetType().FullName -expected "System.String"
        Assert-Equals -actual ($dir_entry -in (
            "$directory_path\subdir-1",
            "$directory_path\subdir-1\subdir-3",
            "$directory_path\subdir-2",
            "$directory_path\acl-dir",
            "$directory_path\file.txt",
            "$directory_path\anotherfile.txt",
            "$directory_path\subdir-1\file-1.txt",
            "$directory_path\subdir-1\subdir-3\file-3.txt",
            "$directory_path\subdir-2\file-2.txt")) -expected $true
    }
    
    $dir_entries = [Ansible.IO.Directory]::GetFileSystemInfos($directory_path)
    Assert-Equals -actual ($dir_entries.Count) -expected 5
    foreach ($dir_entry in $dir_entries) {
        Assert-Equals -actual $dir_entry.GetType().FullName -expected "System.String"
        Assert-Equals -actual ($dir_entry -in (
            "$directory_path\subdir-1",
            "$directory_path\subdir-2",
            "$directory_path\acl-dir",
            "$directory_path\file.txt",
            "$directory_path\anotherfile.txt")) -expected $true
    }
    $dir_entries = [Ansible.IO.Directory]::GetFileSystemInfos($directory_path, "another*")
    Assert-Equals -actual ($dir_entries.Count) -expected 1
    foreach ($dir_entry in $dir_entries) {
        Assert-Equals -actual $dir_entry.GetType().FullName -expected "System.String"
        Assert-Equals -actual ($dir_entry -in ("$directory_path\anotherfile.txt")) -expected $true
    }
    $dir_entries = [Ansible.IO.Directory]::GetFileSystemInfos($directory_path, "*", [System.IO.SearchOption]::AllDirectories)
    Assert-Equals -actual ($dir_entries.Count) -expected 9
    foreach ($dir_entry in $dir_entries) {
        Assert-Equals -actual $dir_entry.GetType().FullName -expected "System.String"
        Assert-Equals -actual ($dir_entry -in (
            "$directory_path\subdir-1",
            "$directory_path\subdir-1\subdir-3",
            "$directory_path\subdir-2",
            "$directory_path\acl-dir",
            "$directory_path\file.txt",
            "$directory_path\anotherfile.txt",
            "$directory_path\subdir-1\file-1.txt",
            "$directory_path\subdir-1\subdir-3\file-3.txt",
            "$directory_path\subdir-2\file-2.txt")) -expected $true
    }

    [Ansible.IO.Directory]::Move("$directory_path\subdir-1", "$directory_path\moved-dir")
    Assert-Equals -actual ([Ansible.IO.Directory]::Exists("$directory_path\subdir-1")) -expected $false
    Assert-Equals -actual ([Ansible.IO.Directory]::Exists("$directory_path\moved-dir")) -expected $true
    
    $parent_dir = [Ansible.IO.Directory]::GetParent("$directory_path\moved-dir")
    Assert-Equals -actual $parent_dir.GetType().FullName -expected "Ansible.IO.DirectoryInfo"
    Assert-Equals -actual $parent_dir.Fullname -expected $directory_path

    [Ansible.IO.Directory]::Delete("$directory_path\acl-dir")
    Assert-Equals -actual ([Ansible.IO.Directory]::Exists("$directory_path\acl-dir")) -expected $false
    $failed = $false
    try {
        [Ansible.IO.Directory]::Delete("$directory_path\moved-dir")
    } catch {
        $failed = $true
        Assert-Equals -actual $_.Exception.Message -expected "Exception calling `"Delete`" with `"1`" argument(s): `"RemoveDirectoryW($directory_path\moved-dir) failed (The directory is not empty, Win32ErrorCode 145)`""
    }
    Assert-Equals -actual $failed -expected $true
    Assert-Equals -actual ([Ansible.IO.Directory]::Exists("$directory_path\moved-dir")) -expected $true
    Assert-Equals -actual ([Ansible.IO.Directory]::Exists("$directory_path\moved-dir\subdir-3")) -expected $true
    Assert-Equals -actual ([Ansible.IO.File]::Exists("$directory_path\moved-dir\file-1.txt")) -expected $true
    Assert-Equals -actual ([Ansible.IO.File]::Exists("$directory_path\moved-dir\subdir-3\file-3.txt")) -expected $true

    [Ansible.IO.Directory]::Delete("$directory_path\moved-dir", $true)
    Assert-Equals -actual ([Ansible.IO.Directory]::Exists("$directory_path\moved-dir")) -expected $false

    $current_time = (Get-Date).ToFileTimeUtc()
    [Ansible.IO.Directory]::CreateDirectory("$directory_path\date") > $null

    $creation_time = [Ansible.IO.Directory]::GetCreationTimeUtc("$directory_path\date")
    Assert-Equals -actual $creation_time.GetType().FullName -expected "System.DateTime"
    Assert-Equals -actual ($creation_time.ToFileTimeUtc() -ge $current_time) -expected $true

    $lastaccess_time = [Ansible.IO.Directory]::GetLastAccessTimeUtc("$directory_path\date")
    Assert-Equals -actual $lastaccess_time.GetType().FullName -expected "System.DateTime"
    Assert-Equals -actual ($lastaccess_time.ToFileTimeUtc() -ge $current_time) -expected $true

    $lastwrite_time = [Ansible.IO.Directory]::GetLastWriteTimeUtc("$directory_path\date")
    Assert-Equals -actual $lastwrite_time.GetType().FullName -expected "System.DateTime"
    Assert-Equals -actual ($lastwrite_time.ToFileTimeUtc() -ge $current_time) -expected $true

    [Ansible.IO.Directory]::SetCreationTimeUtc("$directory_path\date", $new_date)
    $creation_time = [Ansible.IO.Directory]::GetCreationTimeUtc("$directory_path\date")
    Assert-Equals -actual $creation_time -expected $new_date

    [Ansible.IO.Directory]::SetLastAccessTimeUtc("$directory_path\date", $new_date)
    $lastaccess_time = [Ansible.IO.Directory]::GetLastAccessTimeUtc("$directory_path\date")
    Assert-Equals -actual $lastaccess_time -expected $new_date

    [Ansible.IO.Directory]::SetLastWriteTimeUtc("$directory_path\date", $new_date)
    $lastwrite_time = [Ansible.IO.Directory]::GetLastWriteTimeUtc("$directory_path\date")
    Assert-Equals -actual $lastwrite_time -expected $new_date
}

# call each test three times
# 1 - Normal Path
# 2 - Normal Path with the \\?\ prefix
# 3 - Path exceeding 260 chars with the \\?\ prefix
Clear-TestDirectory -path $path
Test-FileClass -root_path $path
Test-DirectoryClass -root_path $path

Clear-TestDirectory -path $path
Test-FileClass -root_path "\\?\$path"
Test-DirectoryClass -root_path "\\?\$path"

Clear-TestDirectory -path $path
$long_path = "\\?\$path\long-path-test\$("a" * 240)"
[Ansible.IO.Directory]::CreateDirectory($long_path) > $null
Test-FileClass -root_path $long_path
Test-DirectoryClass -root_path $long_path

[Ansible.IO.Directory]::Delete("\\?\" + $path, $true) > $null
$result.data = "success"
Exit-Json -obj $result

