#!/bin/bash

# Script de test pour l API ProxmoxMCP avec authentification
# Usage: ./test-api.sh

# Charger la cle API depuis .env
if [ -f .env ]; then
    API_KEY=$(grep MCPO_API_KEY .env | cut -d= -f2)
else
    echo "Erreur: Fichier .env introuvable"
    exit 1
fi

# Configuration
API_URL="http://localhost:8811"
HEADERS=(-H "Content-Type: application/json" -H "Authorization: Bearer $API_KEY")

echo "=== Test API ProxmoxMCP avec authentification ==="
echo ""

# Test 1: Lister les nodes
echo "1. Lister les nodes Proxmox..."
curl -s -X POST "$API_URL/get_nodes" "${HEADERS[@]}" -d "{}"
echo -e "\n"

# Test 2: Obtenir le statut d un node
echo "2. Obtenir le statut du node pve01..."
curl -s -X POST "$API_URL/get_node_status" "${HEADERS[@]}" -d "{\"node\": \"pve01\"}"
echo -e "\n"

# Test 3: Lister les VMs
echo "3. Lister les VMs..."
curl -s -X POST "$API_URL/get_vms" "${HEADERS[@]}" -d "{}"
echo -e "\n"

# Test 4: Lister le storage
echo "4. Lister le storage..."
curl -s -X POST "$API_URL/get_storage" "${HEADERS[@]}" -d "{}"
echo -e "\n"

# Test 5: Obtenir le statut du cluster
echo "5. Obtenir le statut du cluster..."
curl -s -X POST "$API_URL/get_cluster_status" "${HEADERS[@]}" -d "{}"
echo -e "\n"

echo "=== Tests termines ==="
