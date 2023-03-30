import PyInstaller.__main__

PyInstaller.__main__.run([
    'tinet-bridge.py',
    '--onefile',
    '--windowed',
    '--name', 'tinet-bridge.exe',
    '--distpath', '.'
])