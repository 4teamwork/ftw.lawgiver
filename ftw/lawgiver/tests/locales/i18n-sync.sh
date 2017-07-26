#!/usr/bin/env sh

set -eu -o pipefail

for potfile in *.pot; do
  domain=${potfile%.*}
  pofiles=$(find . -name "$domain.po")
  ../../../../bin/i18ndude sync -p $potfile $pofiles
done
