# Run: python -m PyInstaller --noconfirm blue_whale_pet.spec
from pathlib import Path
import PySide6

root=Path(SPECPATH)
assets=root/'src'/'blue_whale_pet'/'assets'
a=Analysis([str(root/'run_pet.py')],pathex=[str(root/'src')],
           binaries=[],datas=[(str(p),'blue_whale_pet/assets') for p in assets.glob('*.png')],
           hiddenimports=[],hookspath=[],hooksconfig={},runtime_hooks=[],
           excludes=['numpy','tkinter'],noarchive=False,optimize=0)
# Avoid inconsistent copies of the MSVC runtime from the build environment.
qt_dir=Path(PySide6.__file__).resolve().parent
runtime={p.name.lower():str(p) for p in qt_dir.glob('*140*.dll')}
a.binaries=[(dest,runtime.get(Path(dest).name.lower(),src),kind)
            for dest,src,kind in a.binaries]
for name,path in runtime.items():
    if not any(dest.lower()==name for dest,_,_ in a.binaries):
        a.binaries.append((name,path,'BINARY'))
# Qt uses Windows ICU. Poppler's similarly named DLL has incompatible exports.
a.binaries=[entry for entry in a.binaries
            if Path(entry[0]).name.lower() not in ('icuuc.dll','icudt78.dll')]
pyz=PYZ(a.pure)
exe=EXE(pyz,a.scripts,a.binaries,a.datas,[],name='BlueWhalePet',
        debug=False,bootloader_ignore_signals=False,strip=False,upx=True,
        upx_exclude=[],runtime_tmpdir=None,console=False,
        disable_windowed_traceback=False,argv_emulation=False,
        target_arch=None,codesign_identity=None,entitlements_file=None)
