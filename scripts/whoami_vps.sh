#!/usr/bin/env bash
# Confirme l'identite reelle du serveur sur lequel ce script tourne :
# hostname, IP publique (vue depuis l'exterieur), et date/heure systeme.
# Utile pour verifier qu'on est bien sur le meme serveur que celui vise
# par le nom de domaine lacaveducoin.com.
# Usage : bash scripts/whoami_vps.sh
set -euo pipefail

echo "=== Hostname ==="
hostname

echo
echo "=== IP publique (vue depuis l'exterieur) ==="
curl -s https://api.ipify.org
echo

echo
echo "=== IP publique (metadonnees Hetzner) ==="
curl -s http://169.254.169.254/hetzner/v1/metadata/public-ipv4 || true
echo

echo
echo "=== Date/heure systeme ==="
date

echo
echo "=== Repertoire courant ==="
pwd
