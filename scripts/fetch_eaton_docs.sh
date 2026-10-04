#!/usr/bin/env bash
# Download Eaton's official Network-M2/M3 API and user documentation used by
# docs/control-api/README.md. Vendor documents are not redistributed in this
# repository; they land in docs/vendor/, which is git-ignored.
#
# Usage: scripts/fetch_eaton_docs.sh [output-dir]
set -euo pipefail

out="${1:-docs/vendor}"
mkdir -p "$out"

eaton="https://www.eaton.com/content/dam/eaton/products/backup-power-ups-surge-it-power-distribution"
conn="$eaton/power-management-software-connectivity"
postman="https://documenter.gw.postman.com/api/collections/7058770"

fetch() {
  local name="$1" url="$2"
  echo "-> $name"
  curl -fsSL --retry 2 -A "Mozilla/5.0" -o "$out/$name" "$url" || echo "   FAILED: $url" >&2
}

# Postman collections (raw JSON behind the documenter pages)
fetch postman-network-m3-rest-2.0.json "$postman/2sAYdmmTha?segregateAuth=true&versionTag=latest"
fetch postman-network-m2-rest-1.0.json "$postman/2sAYBSjt7J?segregateAuth=true&versionTag=latest"
fetch postman-rack-pdu-g4.json        "$postman/2sAYHxo4T9?segregateAuth=true&versionTag=latest"

# User guides
fetch network-m3-user-guide.pdf "$conn/eaton-gigabit-network-card/network-m3/resources/eaton-network-m3-user-guide.pdf"
fetch network-m2-user-guide.pdf "$conn/eaton-gigabit-network-card/eaton-network-m2-user-guide.pdf"

# Release notes
fetch release-notes-network-m2-3.0.5.txt "$conn/release-notes-network-m2-305.txt"
fetch release-notes-network-m2-2.0.5.txt "$conn/Release_Notes_NetworkM2_205.txt"
fetch release-notes-network-m2-1.7.5.txt "$conn/Release_Notes_NetworkM2_INDGWM2_175-399.txt"
fetch release-notes-ipp.txt "$conn/eaton-intelligent-power-protector/eaton-ipp-software-release-notes.txt"
fetch release-notes-ipm.txt "$conn/eaton-intelligent-power-manager/release-notes/eaton-ipm-software-release-notes.txt"

echo
echo "Done. Postman JSON is the collection format (item tree), not the documenter"
echo "'data' export that scripts/convert_postman_to_openapi.py currently reads."
ls -la "$out"
