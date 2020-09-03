param([Parameter(Mandatory=$True)][string]$lp,
      [Parameter(Mandatory=$True)][string]$path,
      [Parameter(Mandatory=$True)][string]$type)

Write-Output "Uploading files for language pair $lp"
$languagePath = $lp.Replace(':', '_')
Get-ChildItem "$path" -Filter *.$languagePath.* |
Foreach-Object {
    Write-Output $_.FullName
    $name = $_.BaseName + "-" + $env:GitVersion_ShortSha
    translator document upload -lp $lp -ws $env:WorkspaceId -dt $type -c $_.FullName --wait -pn "$name" -o
    }