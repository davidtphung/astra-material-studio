"""Package only the add-on and public documentation, never local test fixtures."""
from pathlib import Path
import zipfile,shutil
root=Path(__file__).resolve().parents[1]
out=root/'web/downloads'
out.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(out/'astra.zip','w',zipfile.ZIP_DEFLATED) as archive:
    for path in sorted((root/'astra').glob('*.py')):
        archive.write(path,path.relative_to(root))
    archive.write(root/'README.md','astra/README.md')
    archive.write(root/'ASSET_LICENSES.md','astra/ASSET_LICENSES.md')
for name in ['blender-preview.png','validation.json']:
    source=root/'artifacts'/name
    if source.is_file():
        shutil.copy2(source,out/name)
print('Packaged:',out/'astra.zip')
