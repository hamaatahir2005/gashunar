# Build from the project root: python -m PyInstaller --clean --noconfirm packaging/gas-hunar.spec
from pathlib import Path
root=Path(SPECPATH).parent
analysis=Analysis([str(root/'main.py')],pathex=[str(root)],
    binaries=[],datas=[(str(root/'assets'),'assets')],
    hiddenimports=['arabic_reshaper','bidi.algorithm','sqlalchemy.dialects.sqlite'],
    hookspath=[],hooksconfig={},runtime_hooks=[],excludes=['tkinter','matplotlib','pandas','IPython','pytest'],noarchive=False)
pyz=PYZ(analysis.pure)
exe=EXE(pyz,analysis.scripts,analysis.binaries,analysis.datas,[],
    name='GAS HUNAR',debug=False,bootloader_ignore_signals=False,strip=False,upx=False,
    console=False,disable_windowed_traceback=False,icon=str(root/'assets/gas-hunar.ico'),
    version=str(root/'packaging/version_info.txt'))
