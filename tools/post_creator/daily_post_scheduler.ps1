# daily_post_scheduler.ps1
# Runs the Daily LinkedIn Post & High-Res Image Pipeline

param (
    [string]$Topic = "Building Scalable AI Agent Systems & MCP Automation",
    [string]$Tone = "thought-leadership"
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host " 🚀 LinkedIn Daily Post & High-Res Image Pipeline" -ForegroundColor White
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "Topic: $Topic" -ForegroundColor Yellow
Write-Host "Tone : $Tone" -ForegroundColor Yellow
Write-Host "Engine: FLUX.1 (Photorealistic / High Quality)" -ForegroundColor Green
Write-Host "-----------------------------------------------------"

# Define Python execution snippet
$PythonCmd = @"
import sys, os, json
sys.path.insert(0, r'$ScriptDir')
from post_generator import LinkedInPostGenerator
from image_studio import create_high_res_image
from linkedin_publisher import LinkedInPublisher

topic = r'$Topic'
tone = r'$Tone'

print('[1/3] Generating post copy & visual prompt...')
bundle = LinkedInPostGenerator.craft_post(topic=topic, tone=tone)
draft_path = LinkedInPostGenerator.save_draft(bundle)

print('[2/3] Rendering top-tier FLUX.1 visual...')
img_res = create_high_res_image(prompt=bundle['image_prompt'], aspect_ratio='4:5')

print('[3/3] Bundling complete post package...')
pkg = LinkedInPublisher.package_post(bundle, img_res)
pub = LinkedInPublisher.publish_package(pkg)

print('\nSUCCESS! Package ready at:', pkg['package_file'])
print('Rendered image at:', img_res['file_path'])
"@

python -c "$PythonCmd"

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ Pipeline completed successfully!" -ForegroundColor Green
} else {
    Write-Host "`n❌ Pipeline failed." -ForegroundColor Red
}
