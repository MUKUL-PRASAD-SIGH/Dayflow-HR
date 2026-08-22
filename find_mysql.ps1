# PowerShell script to find and manage MySQL services

# Get all services that might be related to MySQL
$mysqlServices = Get-Service | Where-Object { $_.DisplayName -like '*mysql*' -or $_.Name -like '*mysql*' }

if ($mysqlServices) {
    Write-Host "Found MySQL-related services:"
    Write-Host "---------------------------"
    
    foreach ($service in $mysqlServices) {
        $status = $service.Status
        $startType = $service.StartType
        
        Write-Host "Service Name: $($service.Name)"
        Write-Host "Display Name: $($service.DisplayName)"
        Write-Host "Status: $status"
        Write-Host "Start Type: $startType"
        Write-Host "---------------------------"
        
        # If service is not running, offer to start it
        if ($status -ne 'Running') {
            $start = Read-Host "Do you want to start this service? (Y/N)"
            if ($start -eq 'Y' -or $start -eq 'y') {
                try {
                    Start-Service -Name $service.Name -ErrorAction Stop
                    Write-Host "Successfully started $($service.DisplayName)" -ForegroundColor Green
                } catch {
                    Write-Host "Failed to start $($service.DisplayName): $_" -ForegroundColor Red
                }
            }
        }
    }
} else {
    Write-Host "No MySQL services found on this system." -ForegroundColor Yellow
    Write-Host "You may need to install MySQL Server first."
}

# Check if MySQL is in PATH
$mysqlPath = Get-Command mysql -ErrorAction SilentlyContinue
if ($mysqlPath) {
    Write-Host "`nMySQL client is available at: $($mysqlPath.Source)" -ForegroundColor Green
} else {
    Write-Host "`nMySQL client is not in your system PATH." -ForegroundColor Yellow
}

# Check if MySQL is running on default port
$mysqlPort = Test-NetConnection -ComputerName localhost -Port 3306
if ($mysqlPort.TcpTestSucceeded) {
    Write-Host "`nMySQL is running on port 3306" -ForegroundColor Green
} else {
    Write-Host "`nMySQL is not running on port 3306" -ForegroundColor Yellow
}

# Check common MySQL installation paths
$commonPaths = @(
    "C:\Program Files\MySQL",
    "C:\Program Files (x86)\MySQL",
    "${env:ProgramFiles}\MySQL",
    "${env:ProgramFiles(x86)}\MySQL"
)

Write-Host "`nChecking common MySQL installation paths..."
$found = $false
foreach ($path in $commonPaths) {
    if (Test-Path $path) {
        Write-Host "Found MySQL installation at: $path" -ForegroundColor Green
        $found = $true
    }
}

if (-not $found) {
    Write-Host "No MySQL installation found in common locations." -ForegroundColor Yellow
}
