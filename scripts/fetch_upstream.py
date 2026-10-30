"""Clone the public, known-good NexusDesk commit without storing a copy in CloudForge.

Usage: python scripts/fetch_upstream.py
Requires git. Rejects an existing unrecognized checkout; does not update it.
"""
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'upstream'/'NexusDesk'
REF=(ROOT/'UPSTREAM_VERSION').read_text().split('COMMIT=')[1].splitlines()[0].strip()
REPO=(ROOT/'UPSTREAM_VERSION').read_text().split('REPOSITORY=')[1].splitlines()[0].strip()
URL='https://github.com/'+REPO+'.git'


def run(*args):
    return subprocess.check_output(args, text=True).strip()


def main():
    if DEST.exists():
        if not (DEST/'.git').exists():
            raise SystemExit('Expected a Git checkout at '+str(DEST))
    else:
        DEST.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(['git','clone','--filter=blob:none','--no-checkout',URL,str(DEST)],check=True)
    subprocess.run(['git','-C',str(DEST),'fetch','--depth','1','origin',REF],check=True)
    subprocess.run(['git','-C',str(DEST),'checkout','--detach',REF],check=True)
    actual=run('git','-C',str(DEST),'rev-parse','HEAD')
    if actual!=REF:
        raise SystemExit('Pinned NexusDesk SHA mismatch')
    print(f'Pinned NexusDesk source ready: {actual}')

if __name__=='__main__':
    main()
