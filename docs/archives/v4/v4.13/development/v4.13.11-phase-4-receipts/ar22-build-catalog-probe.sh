#!/usr/bin/env bash
set -uo pipefail
export PATH=/opt/python/cp312-cp312/bin:$PATH
cd /w
snap() { find data -type f -print0 | sort -z | xargs -0 sha256sum; }
make --version | head -1
python --version
snap > /tmp/before.txt
make build-catalog > /tmp/refuse.out 2>&1; rc=$?
snap > /tmp/after.txt
echo "REFUSE exit=$rc"; cat /tmp/refuse.out
if cmp -s /tmp/before.txt /tmp/after.txt; then echo "REFUSE data unchanged: yes"; else echo "REFUSE data unchanged: NO"; fi
echo "data files hashed: $(wc -l < /tmp/before.txt)"
make build-catalog FORCE=1 > /tmp/force.out 2>&1; rc2=$?
snap > /tmp/forced.txt
echo "FORCE exit=$rc2"; tail -5 /tmp/force.out
echo "FORCE changed data files: $(diff /tmp/before.txt /tmp/forced.txt | grep -c '^>')"
