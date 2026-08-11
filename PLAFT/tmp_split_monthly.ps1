$baseTest2 = "C:\Users\b46637\OneDrive - Interbank\PLAFT\Interbank\PLAFT\Desarrollo\Minorista_regulado\Bases\test_2\test_total.csv"
$baseExtras = "C:\Users\b46637\OneDrive - Interbank\PLAFT\Interbank\PLAFT\Desarrollo\Minorista_regulado\Bases\test\extras_test_total.csv"
$months = @(202509,202510,202511,202512,202601,202602,202603,202604)
$monthSet = @{}; foreach($m in $months){ $monthSet[$m] = $true }
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)

if (!(Test-Path $baseTest2)) { throw "No existe: $baseTest2" }
if (!(Test-Path $baseExtras)) { throw "No existe: $baseExtras" }

$extrasDir = Split-Path -Parent $baseExtras
$extrasBase = [System.IO.Path]::GetFileNameWithoutExtension($baseExtras)
$extrasExt = [System.IO.Path]::GetExtension($baseExtras)
$test2Dir = Split-Path -Parent $baseTest2
$test2Base = [System.IO.Path]::GetFileNameWithoutExtension($baseTest2)
$test2Ext = [System.IO.Path]::GetExtension($baseTest2)

$srExtras = [System.IO.StreamReader]::new($baseExtras)
$extrasWriters = @{}
$extrasCounts = @{}
foreach($m in $months){
  $out = Join-Path $extrasDir ("{0}_{1}{2}" -f $extrasBase,$m,$extrasExt)
  $extrasWriters[$m] = [System.IO.StreamWriter]::new($out,$false,$utf8NoBom)
  $extrasCounts[$m] = 0
}
try {
  $header = $srExtras.ReadLine()
  if ($null -eq $header) { throw "Archivo vacio: $baseExtras" }
  foreach($m in $months){ $extrasWriters[$m].WriteLine($header) }

  while(($line = $srExtras.ReadLine()) -ne $null){
    $first = $line.Split(',',2)[0]
    $m = [int][double]$first
    if($monthSet.ContainsKey($m)){
      $extrasWriters[$m].WriteLine($line)
      $extrasCounts[$m]++
    }
  }
}
finally {
  $srExtras.Close()
  foreach($m in $months){ $extrasWriters[$m].Close() }
}

$srTest = [System.IO.StreamReader]::new($baseTest2)
$srExtras2 = [System.IO.StreamReader]::new($baseExtras)
$testWriters = @{}
$testCounts = @{}
foreach($m in $months){
  $out = Join-Path $test2Dir ("{0}_{1}{2}" -f $test2Base,$m,$test2Ext)
  $testWriters[$m] = [System.IO.StreamWriter]::new($out,$false,$utf8NoBom)
  $testCounts[$m] = 0
}
try {
  $null = $srExtras2.ReadLine()
  while($true){
    $lineTest = $srTest.ReadLine()
    $lineExtras = $srExtras2.ReadLine()
    if($null -eq $lineTest -or $null -eq $lineExtras){ break }
    $first = $lineExtras.Split(',',2)[0]
    $m = [int][double]$first
    if($monthSet.ContainsKey($m)){
      $testWriters[$m].WriteLine($lineTest)
      $testCounts[$m]++
    }
  }
}
finally {
  $srTest.Close(); $srExtras2.Close()
  foreach($m in $months){ $testWriters[$m].Close() }
}

foreach($m in $months){
  $p1 = Join-Path $extrasDir ("{0}_{1}{2}" -f $extrasBase,$m,$extrasExt)
  $p2 = Join-Path $test2Dir ("{0}_{1}{2}" -f $test2Base,$m,$test2Ext)
  Write-Output ("OK|"+$extrasCounts[$m]+"|"+$p1)
  Write-Output ("OK|"+$testCounts[$m]+"|"+$p2)
}
