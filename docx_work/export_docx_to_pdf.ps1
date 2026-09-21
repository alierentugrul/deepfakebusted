$ErrorActionPreference = "Stop"

$docxPath = Join-Path (Resolve-Path ".").Path "taslak_Journal_paper.docx"
$outDir = Join-Path (Resolve-Path ".").Path "docx_render_check\journal_after_word"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$pdfPath = Join-Path $outDir "taslak_Journal_paper.pdf"

$word = $null
$doc = $null
try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $doc = $word.Documents.Open($docxPath, $false, $true)
    $doc.ExportAsFixedFormat($pdfPath, 17)
    Write-Output $pdfPath
}
finally {
    if ($doc -ne $null) {
        $doc.Close($false)
        [System.Runtime.InteropServices.Marshal]::ReleaseComObject($doc) | Out-Null
    }
    if ($word -ne $null) {
        $word.Quit()
        [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
    }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}
