#!/usr/bin/env python3
"""Download the public official March 7th MMD reference into ignored local storage.

Original publication: https://www.bilibili.com/blackboard/activity-Hk1xELkY1x.html
Preserves the original archive and usage notice; does not redistribute the model.
"""
import hashlib
import os
from pathlib import Path, PurePosixPath
import stat
import tempfile
import urllib.request
import zipfile

URL = 'https://activity.hdslb.com/blackboard/static/20221205/d7f098333308ba7412aa9b57601bfa1d/KkVjYLh8y3.zip'
SHA256 = '4256b27d90175166460d6ef31d23b3e0ea163d351ad25881a90d87f4d7c41483'
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'projects/honkai-star-rail/march-7th-preservation-bjd-1-4/references/local/official-models'
LIMIT = 64 * 1024 * 1024


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    archive = OUT / 'march-7th-preservation-official.zip'
    if not archive.exists():
        request = urllib.request.Request(URL, headers={'User-Agent': 'Mozilla/5.0'})
        temporary = None
        try:
            with urllib.request.urlopen(request, timeout=45) as response, tempfile.NamedTemporaryFile(dir=OUT, suffix='.part', delete=False) as f:
                temporary = Path(f.name)
                total = 0
                while True:
                    chunk = response.read(1024*1024)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > LIMIT:
                        raise ValueError('Archive exceeds expected maximum size')
                    f.write(chunk)
            if digest(temporary) != SHA256:
                raise ValueError('Official archive changed: inspect source and usage terms before updating checksum')
            os.replace(temporary, archive)
        finally:
            if temporary is not None and temporary.exists():
                temporary.unlink()
    if digest(archive) != SHA256:
        raise ValueError('Existing ZIP checksum mismatch; refusing to overwrite')
    destination = OUT / 'extracted'
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None:
            raise ValueError('ZIP CRC verification failed')
        if sum(i.file_size for i in z.infolist()) > LIMIT:
            raise ValueError('Uncompressed archive exceeds limit')
        files = []
        for info in z.infolist():
            name = info.filename if info.flag_bits & 0x800 else info.filename.encode('cp437').decode('gbk')
            relative = PurePosixPath(name.replace('\\', '/'))
            if relative.is_absolute() or '..' in relative.parts or (relative.parts and ':' in relative.parts[0]):
                raise ValueError('Unsafe archive path')
            if stat.S_ISLNK(info.external_attr >> 16):
                raise ValueError('Archive symlink is not allowed')
            target = destination.joinpath(*relative.parts)
            if not target.resolve().is_relative_to(destination.resolve()):
                raise ValueError('Target escapes reference directory')
            if info.is_dir():
                continue
            data = z.read(info)
            if target.exists() and target.read_bytes() != data:
                raise ValueError(f'Existing file differs; preserve local edit: {relative}')
            files.append((target, data))
        for target, data in files:
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                target.write_bytes(data)
    print(f'Verified {len(files)} files in {destination}')
    print('Read the original 使用规则.txt before using the reference model.')


if __name__ == '__main__':
    main()
