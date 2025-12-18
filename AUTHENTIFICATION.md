# Configuration de l authentification ProxmoxMCP

## Vue d ensemble

ProxmoxMCP utilise **mcpo** (MCP-to-OpenAPI proxy) avec authentification par cle API pour securiser l acces a l API REST.

## Configuration

### 1. Cle API

La cle API est stockee dans le fichier `.env` :

```bash
# Voir la cle actuelle
cat .env

# Generer une nouvelle cle securisee
echo "MCPO_API_KEY=$(openssl rand -hex 32)" > .env
```

### 2. Variables d environnement

Le fichier `.env` est automatiquement charge par docker-compose :

- `MCPO_API_KEY` : Cle API pour l authentification (OBLIGATOIRE)
- `PROXMOX_MCP_CONFIG` : Chemin vers le fichier de configuration Proxmox

## Utilisation de l API

### Sans authentification (REJETE)

```bash
curl -X POST http://localhost:8811/get_nodes -H "Content-Type: application/json" -d "{}"
# Reponse : {"detail":"Missing or invalid Authorization header"}
```

### Avec authentification (ACCEPTE)

```bash
# Recuperer la cle API
API_KEY=$(grep MCPO_API_KEY .env | cut -d= -f2)

# Faire un appel authentifie
curl -X POST http://localhost:8811/get_nodes \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d "{}"
```

## Exemples d appels API

### Lister les nodes
```bash
curl -X POST http://192.168.1.127:8811/get_nodes \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" -d "{}"
```

### Obtenir le statut d un node
```bash
curl -X POST http://192.168.1.127:8811/get_node_status \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"node\": \"pve01\"}"
```

### Lister les VMs
```bash
curl -X POST http://192.168.1.127:8811/get_vms \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" -d "{}"
```

## Securite

### Limiter l acces reseau

**1. Utiliser un reverse proxy (Nginx/Traefik) avec filtrage IP**

**2. Utiliser Docker networks pour isoler le container**

**3. Utiliser un firewall (iptables/ufw)** :
```bash
# Autoriser uniquement depuis localhost
sudo ufw allow from 127.0.0.1 to any port 8811

# Ou depuis un reseau specifique
sudo ufw allow from 192.168.1.0/24 to any port 8811
```

## Documentation complete

- **Swagger UI** : http://192.168.1.127:8811/docs
- **OpenAPI JSON** : http://192.168.1.127:8811/openapi.json
- **GitHub mcpo** : https://github.com/open-webui/mcpo

## Changer la cle API

```bash
# 1. Generer une nouvelle cle
echo "MCPO_API_KEY=$(openssl rand -hex 32)" > .env

# 2. Redemarrer le container
docker compose restart
```

## Securite - Bonnes pratiques

1. NE JAMAIS commiter le fichier .env dans git
2. TOUJOURS utiliser HTTPS en production (reverse proxy avec SSL/TLS)
3. CHANGER la cle API par defaut avant la mise en production
4. LIMITER l acces reseau avec un firewall
5. SURVEILLER les logs : docker compose logs -f

## Depannage

### Erreur : "Missing or invalid Authorization header"
Vous n avez pas fourni le header Authorization

### Erreur : "Invalid API key"
La cle API est incorrecte. Verifier avec : cat .env

---

## IMPORTANT: Comment appliquer les changements du fichier .env

**ATTENTION** : Un simple `docker compose restart` ne suffit PAS pour recharger les variables du fichier .env !

### Methode correcte pour appliquer les changements

```bash
cd /home/rateur42/proxmoxMCP

# IMPORTANT: Faire un down puis up (pas juste restart)
docker compose down
docker compose up -d

# Attendre quelques secondes
sleep 5

# Verifier que la nouvelle cle est active
docker compose exec proxmox-mcp-api printenv MCPO_API_KEY
```

### Pourquoi ?

- `docker compose restart` : Redémarre le container mais garde les anciennes variables d environnement
- `docker compose down && up` : Détruit et recrée le container avec les nouvelles variables

### Verification rapide

```bash
# Verifier la cle dans le fichier .env
cat .env

# Verifier la cle dans le container en cours d execution
docker compose exec proxmox-mcp-api printenv MCPO_API_KEY

# Les deux doivent etre identiques !
```

### Test complet apres modification

```bash
cd /home/rateur42/proxmoxMCP

# 1. Modifier le .env
echo "MCPO_API_KEY=$(openssl rand -hex 32)" > .env

# 2. Appliquer les changements (DOWN puis UP, pas restart !)
docker compose down && docker compose up -d && sleep 5

# 3. Tester avec la nouvelle cle
./test-api.sh
```
