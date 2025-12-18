# Guide de demarrage rapide - ProxmoxMCP avec authentification

## Votre cle API

Votre cle API actuelle :
```bash
cat /home/rateur42/proxmoxMCP/.env
```

Resultat : `MCPO_API_KEY=1e62c690441f8b3544c59b8a5b233de2fc8735dc10c179f2a5432e830df90141`

## Test rapide

### Depuis le serveur SSH

```bash
cd /home/rateur42/proxmoxMCP
./test-api.sh
```

### Depuis votre machine locale

```bash
# Remplacez YOUR_API_KEY par votre vraie cle
curl -X POST http://192.168.1.127:8811/get_vms \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer 1e62c690441f8b3544c59b8a5b233de2fc8735dc10c179f2a5432e830df90141" \
  -d "{}"
```

## Exemples d utilisation

### 1. Lister les nodes Proxmox

```bash
curl -X POST http://192.168.1.127:8811/get_nodes \
  -H "Authorization: Bearer 1e62c690441f8b3544c59b8a5b233de2fc8735dc10c179f2a5432e830df90141" \
  -H "Content-Type: application/json" \
  -d "{}"
```

### 2. Voir le statut d un node

```bash
curl -X POST http://192.168.1.127:8811/get_node_status \
  -H "Authorization: Bearer 1e62c690441f8b3544c59b8a5b233de2fc8735dc10c179f2a5432e830df90141" \
  -H "Content-Type: application/json" \
  -d "{\"node\": \"pve01\"}"
```

### 3. Lister les VMs

```bash
curl -X POST http://192.168.1.127:8811/get_vms \
  -H "Authorization: Bearer 1e62c690441f8b3544c59b8a5b233de2fc8735dc10c179f2a5432e830df90141" \
  -H "Content-Type: application/json" \
  -d "{}"
```

### 4. Demarrer une VM

```bash
curl -X POST http://192.168.1.127:8811/start_vm \
  -H "Authorization: Bearer 1e62c690441f8b3544c59b8a5b233de2fc8735dc10c179f2a5432e830df90141" \
  -H "Content-Type: application/json" \
  -d "{\"node\": \"pve01\", \"vmid\": \"103\"}"
```

### 5. Arreter une VM

```bash
curl -X POST http://192.168.1.127:8811/stop_vm \
  -H "Authorization: Bearer 1e62c690441f8b3544c59b8a5b233de2fc8735dc10c179f2a5432e830df90141" \
  -H "Content-Type: application/json" \
  -d "{\"node\": \"pve01\", \"vmid\": \"103\"}"
```

### 6. Lister les containers LXC

```bash
curl -X POST http://192.168.1.127:8811/get_containers \
  -H "Authorization: Bearer 1e62c690441f8b3544c59b8a5b233de2fc8735dc10c179f2a5432e830df90141" \
  -H "Content-Type: application/json" \
  -d "{\"payload\": {\"node\": null, \"include_stats\": true, \"format_style\": \"pretty\"}}"
```

## Documentation complete

- **Swagger UI** : http://192.168.1.127:8811/docs (interface interactive)
- **OpenAPI JSON** : http://192.168.1.127:8811/openapi.json
- **Documentation authentification** : /home/rateur42/proxmoxMCP/AUTHENTIFICATION.md

## Gestion du container

```bash
cd /home/rateur42/proxmoxMCP

# Voir les logs
docker compose logs -f

# Redemarrer
docker compose down && docker compose up -d

# Arreter
docker compose down

# Statut
docker compose ps
```

## Changer la cle API

```bash
cd /home/rateur42/proxmoxMCP

# 1. Generer nouvelle cle
echo "MCPO_API_KEY=$(openssl rand -hex 32)" > .env

# 2. Appliquer (IMPORTANT: down puis up, pas restart !)
docker compose down && docker compose up -d

# 3. Verifier
sleep 5
docker compose exec proxmox-mcp-api printenv MCPO_API_KEY

# 4. Tester
./test-api.sh
```

## Securite

Votre API est securisee avec :
- Authentification par cle API obligatoire
- Fichier .env avec permissions 600
- Logs d acces disponibles

Pour restreindre l acces :
- Voir AUTHENTIFICATION.md pour configurer un firewall
- Ou modifier docker-compose.yml pour ecouter sur localhost uniquement

## Endpoints disponibles

Tous les endpoints sont documentes sur : http://192.168.1.127:8811/docs

Principaux endpoints :
- /get_nodes - Lister les nodes
- /get_node_status - Statut d un node
- /get_vms - Lister les VMs
- /create_vm - Creer une VM
- /start_vm - Demarrer une VM
- /stop_vm - Arreter une VM
- /shutdown_vm - Eteindre une VM proprement
- /reset_vm - Redemarrer une VM
- /delete_vm - Supprimer une VM
- /execute_vm_command - Executer une commande dans une VM
- /get_containers - Lister les containers LXC
- /start_container - Demarrer un container
- /stop_container - Arreter un container
- /restart_container - Redemarrer un container
- /update_container_resources - Modifier les ressources d un container
- /get_storage - Lister le storage
- /get_cluster_status - Statut du cluster

## Depannage

### Erreur "Invalid API key"

```bash
# Verifier que la cle dans .env est la meme que dans le container
cat .env
docker compose exec proxmox-mcp-api printenv MCPO_API_KEY

# Si different, appliquer les changements
docker compose down && docker compose up -d
```

### Erreur "Missing or invalid Authorization header"

Vous avez oublie le header Authorization. Format correct :
```bash
-H "Authorization: Bearer VOTRE_CLE_API"
```

### Container en erreur

```bash
# Voir les logs
docker compose logs --tail=100

# Verifier le config Proxmox
cat proxmox-config/config.json
```
