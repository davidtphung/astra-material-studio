"""Publish a committed build to the existing gh-pages branch, without force-push."""
from pathlib import Path
import shutil
import subprocess
import tempfile

root=Path(__file__).resolve().parents[1]

def run(args,cwd=root,output=False):
    result=subprocess.run(args,cwd=cwd,check=True,text=True,capture_output=output)
    return result.stdout.strip() if output else None

if run(['git','status','--porcelain'],output=True):
    raise SystemExit('Commit source changes before publishing.')
remote=run(['git','remote','get-url','origin'],output=True)
if remote!='https://github.com/davidtphung/astra-material-studio.git':
    raise SystemExit('Unexpected repository target; inspect the origin before publishing.')
sha=run(['git','rev-parse','HEAD'],output=True)
run(['npm','run','check'])
run(['npm','run','build'])
auth=['git','-c','credential.helper=','-c','credential.helper=!gh auth git-credential']
with tempfile.TemporaryDirectory(prefix='astra-pages-') as temp:
    destination=Path(temp)/'publish'
    run(auth+['clone','--depth','1','--branch','gh-pages','--single-branch',remote,str(destination)])
    for child in destination.iterdir():
        if child.name=='.git':
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()
    shutil.copytree(root/'dist',destination,dirs_exist_ok=True)
    (destination/'.nojekyll').touch()
    run(['git','add','.'],cwd=destination)
    if not run(['git','diff','--cached','--name-only'],cwd=destination,output=True):
        print('Published branch already matches this build.')
    else:
        run(['git','commit','-m','Publish ASTRA source '+sha],cwd=destination)
        run(auth+['push','origin','gh-pages'],cwd=destination)
print('Push complete. Verify the GitHub Pages deployment before reporting it live.')
