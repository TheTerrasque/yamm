# -*- mode: python -*-

# pyInstaller 2.1 spec file
# https://github.com/pyinstaller/pyinstaller/wiki

a = Analysis(['yammy ui.pyw'],
             #pathex=['c:\\Users\\Mikael\\Documents\\Code\\yamm'],
             pathex=['.'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='yammy ui.exe',
          debug=False,
          strip=None,
          upx=True,
          console=False )
coll = COLLECT(exe,
               a.binaries + [
                ("utils/yamm_plugin_mo.py","utils/yamm_plugin_mo.py", "DATA")
                ],
               a.zipfiles,
               a.datas,
               strip=None,
               upx=True,
               name='yammy ui')
