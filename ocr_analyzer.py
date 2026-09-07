# -*- coding: utf-8 -*-
"""
ocr_analyzer.py — распознавание текста на изображениях/сканах.

Способы (по очереди):
  1) Tesseract (если установлен на компьютере);
  2) Встроенный OCR Windows (Windows.Media.Ocr) — ничего доустанавливать не нужно.
"""
import os
import re
import io
import subprocess
import tempfile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

_WINRT_PS1 = r'''$ErrorActionPreference='Stop'
$path=$args[0]
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
  $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and
  $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
function Await($WinRtTask, $ResultType) {
  $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
  $netTask = $asTask.Invoke($null, @($WinRtTask))
  $netTask.Wait(-1) | Out-Null
  $netTask.Result
}
$null = [Windows.Storage.StorageFile,Windows.Storage,ContentType=WindowsRuntime]
$null = [Windows.Media.Ocr.OcrEngine,Windows.Foundation,ContentType=WindowsRuntime]
$null = [Windows.Graphics.Imaging.BitmapDecoder,Windows.Foundation,ContentType=WindowsRuntime]
$file = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync($path)) ([Windows.Storage.StorageFile])
$stream = Await ($file.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
$decoder = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
$bitmap = Await ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
$engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
if ($engine -eq $null) { Write-Output '__NO_OCR_LANG__'; exit }
$result = Await ($engine.RecognizeAsync($bitmap)) ([Windows.Media.Ocr.OcrResult])
Write-Output $result.Text
'''


def _ocr_tesseract(path):
    try:
        exe = os.environ.get('TESSERACT_CMD', 'tesseract')
        r = subprocess.run([exe, path, 'stdout', '-l', 'rus+eng', '--psm', '6'],
                           capture_output=True, timeout=120)
        if r.returncode == 0:
            return (r.stdout or b'').decode('utf-8', 'ignore').strip()
    except Exception:
        pass
    return ''


def _ocr_windows(path):
    try:
        ps1 = os.path.join(tempfile.gettempdir(), '_grafik_ocr.ps1')
        with io.open(ps1, 'w', encoding='utf-8-sig') as f:
            f.write(_WINRT_PS1)
        r = subprocess.run(
            ['powershell', '-NoProfile', '-NonInteractive', '-ExecutionPolicy',
             'Bypass', '-File', ps1, path],
            capture_output=True, timeout=180)
        out = (r.stdout or b'').decode('utf-8', 'ignore', 'replace').strip()
        if '__NO_OCR_LANG__' in out:
            return ''
        return out
    except Exception:
        return ''


def ocr_image(path):
    """Распознаёт текст с изображения (пробует tesseract, затем Windows OCR)."""
    text = _ocr_tesseract(path)
    if text:
        return text
    return _ocr_windows(path)


def extract_fields(text):
    """Вытаскивает типовые реквизиты из распознанного текста."""
    res = {'text': text}
    m = re.search(r'ИНН[:\s]*(\d{10}|\d{12})', text)
    if m:
        res['inn'] = m.group(1)
    m = re.search(r'ОГРН[:\s]*(\d{13}|\d{15})', text)
    if m:
        res['ogrn'] = m.group(1)
    m = re.search(r'КПП[:\s]*(\d{9})', text)
    if m:
        res['kpp'] = m.group(1)
    m = re.search(r'(\d{3}[- ]?\d{3}[- ]?\d{3}[- ]?\d{2})', text)
    if m:
        res['snils'] = m.group(1)
    m = re.search(r'(?<!\d)(\d{4})\s?(\d{6})(?!\d)', text)
    if m and re.search(r'паспорт|ПАСПОРТ', text, re.I):
        res['passport'] = '%s %s' % (m.group(1), m.group(2))
    return res
