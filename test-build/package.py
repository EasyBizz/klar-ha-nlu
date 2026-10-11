"""Package a prebuilt engine and UI as an isolated, locally installable HA app."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tarfile
import zipfile

arch, binary = sys.argv[1:]
root = Path(__file__).resolve().parents[1]
version = json.loads((root / 'custom_components/klar_nlu/manifest.json').read_text())['version']
out = root / 'dist'
out.mkdir(exist_ok=True)
stage = out / f'klar-test-{arch}'
if stage.exists():
    shutil.rmtree(stage)
app = stage / 'local-apps/klar_nlu_pr289_pr290'
app.mkdir(parents=True)
shutil.copy2(binary, app / 'klar')
(app / 'klar').chmod(0o755)
for name in ['LICENSE', 'THIRD_PARTY']:
    shutil.copy2(root / name, app / name)
shutil.copy2(root / 'scripts/klar-entry.sh', app / 'klar-entry.sh')
shutil.copytree(root / 'web/dist', app / 'ui')
config = (root / 'addon/config.yaml').read_text()
config = config.replace('name: Klar NLU\n', 'name: Klar NLU (PR 289 + 290 Test)\n')
config = config.replace('slug: klar_nlu\n', 'slug: klar_nlu_pr289_pr290\n')
config = config.replace('stage: stable', 'stage: experimental').replace('boot: auto', 'boot: manual')
config = config.replace('hostname: klar-nlu\n', 'hostname: klar-nlu-pr289-pr290\n')
config = config.replace('panel_title: Klar NLU\n', 'panel_title: Klar NLU Test\n')
config = config.replace('  - amd64\n  - aarch64\n', f'  - {arch}\n')
config = '\n'.join(line for line in config.splitlines() if not line.startswith('image:')) + '\n'
(app / 'config.yaml').write_text(config)
# Local installation builds only the runtime wrapper; engine and UI are already built.
shutil.copy2(root / 'docker/Dockerfile', app / 'Dockerfile')
shutil.copy2(root / 'addon/icon.png', app / 'icon.png')
shutil.copytree(root / 'custom_components/klar_nlu', stage / 'custom_components/klar_nlu', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
shutil.copy2(root / 'test-build/INSTALL.md', stage / 'INSTALL.md')
provenance = json.loads((root / 'test-build/provenance.json').read_text())
provenance.update(version=version, architecture=arch)
(stage / 'BUILD.json').write_text(json.dumps(provenance, indent=2) + '\n')
checksums = []
for path in sorted(stage.rglob('*')):
    if path.is_file():
        checksums.append(f'{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(stage)}')
(stage / 'SHA256SUMS').write_text('\n'.join(checksums) + '\n')
archive = out / f'klar-pr289-pr290-{version}-{arch}.tar.gz'
with tarfile.open(archive, 'w:gz') as tar:
    tar.add(stage, arcname=stage.name)
print(archive)
