$docPath = "C:\Users\KIIT0001\Documents\projects\3d2d\traffic\Project_Report_Final.docx"
$pdfPath = "C:\Users\KIIT0001\Documents\projects\3d2d\traffic\Project_Report_Final.pdf"

$word = New-Object -ComObject Word.Application
$word.Visible = $false
try {
    $doc = $word.Documents.Open($docPath)
    $doc.SaveAs([ref]$pdfPath, [ref]17)
    $doc.Close()
    Write-Host "PDF generated successfully!"
} catch {
    Write-Host "Error during conversion: $_"
} finally {
    $word.Quit()
}

