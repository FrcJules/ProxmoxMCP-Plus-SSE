# ProxmoxMCP - MCP Server for Proxmox VE

Serveur MCP (Model Context Protocol) pour gérer Proxmox VE via n8n et autres clients MCP compatibles.

## ✨ Features

- 🔌 **16 Tools Proxmox** pour une gestion complète
- 🔐 **Authentification Bearer Token** sécurisée
- 🐳 **Docker Ready** avec docker-compose
- 📡 **Protocol MCP** avec transport SSE + JSON-RPC 2.0
- 🤖 **Compatible n8n** pour l'automatisation

## 🚀 Quick Start

### 1. Configuration Proxmox

Créez un token API dans Proxmox :

```bash
# Dans Proxmox : Datacenter > Permissions > API Tokens
# Créez un token pour l'utilisateur root@pam
```

Configurez le fichier `proxmox-config/config.json` :

```json
{
  "proxmox": {
    "host": "192.168.1.81",
    "port": 8006,
    "verify_ssl": false,
    "service": "PVE"
  },
  "auth": {
    "user": "root@pam",
    "token_name": "MCP",
    "token_value": "votre-token-api"
  },
  "logging": {
    "level": "INFO",
    "file": "/app/logs/proxmox-mcp.log"
  }
}
```

### 2. Configuration API Key

```bash
# Générer une clé API aléatoire
echo "MCPO_API_KEY=$(openssl rand -hex 32)" > .env
```

### 3. Démarrage

```bash
docker compose up -d
```

## 🔧 Configuration n8n

Pour utiliser ce serveur MCP avec n8n, configurez le nœud **MCP Client Tool** :

- **Server URL** : `http://proxmox-mcp:8812/proxmox/mcp/sse`
- **Server Transport** : `HTTP Streamable`
- **Authentication** : `Bearer Token`
- **Bearer Token** : (la valeur de MCPO_API_KEY dans `.env`)

**Note** : Le conteneur `proxmox-mcp` doit être sur le même réseau Docker que n8n.

## 🛠️ Tools Disponibles

### Nodes Management (2 tools)
- `get_nodes` - Liste tous les nodes du cluster
- `get_node_status` - Statut d'un node spécifique

### Virtual Machines (7 tools)
- `get_vms` - Liste toutes les VMs
- `create_vm` - Créer une nouvelle VM
- `start_vm` - Démarrer une VM
- `stop_vm` - Arrêter une VM (forcé)
- `shutdown_vm` - Arrêt gracieux
- `reset_vm` - Redémarrer une VM
- `delete_vm` - Supprimer une VM

### Storage (1 tool)
- `get_storage` - Liste tous les storages

### Cluster (1 tool)
- `get_cluster_status` - Statut du cluster

### LXC Containers (5 tools)
- `get_containers` - Liste tous les containers
- `start_container` - Démarrer un container
- `stop_container` - Arrêter un container
- `restart_container` - Redémarrer un container
- `update_container_resources` - Modifier les ressources (CPU, RAM, disk)

## 📋 Exemples d'Utilisation

### Via curl

```bash
# Récupérer l'API key
API_KEY=$(grep MCPO_API_KEY .env | cut -d= -f2)

# Lister les VMs
curl -X POST http://localhost:8812/proxmox/mcp/sse \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "get_vms",
      "arguments": {}
    },
    "jsonrpc": "2.0",
    "id": 1
  }'

# Démarrer une VM
curl -X POST http://localhost:8812/proxmox/mcp/sse \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "start_vm",
      "arguments": {
        "node": "pve01",
        "vmid": "100"
      }
    },
    "jsonrpc": "2.0",
    "id": 2
  }'
```

## 🏗️ Architecture

```
Client MCP (n8n, Claude Desktop, etc.)
        │
        │ HTTP + Bearer Auth
        │ JSON-RPC 2.0
        ▼
ProxmoxMCP Server (FastAPI)
        │
        │ - GET /proxmox/mcp/sse → SSE connection
        │ - POST /proxmox/mcp/sse → JSON-RPC messages
        ▼
Proxmox VE API (proxmoxer)
        │
        ▼
Proxmox VE Cluster
```

## 🐳 Docker Compose

Le projet inclut un `docker-compose.yml` prêt à l'emploi. Assurez-vous d'ajouter le serveur au réseau de votre client MCP (par exemple le réseau n8n) :

```yaml
networks:
  n8n_n8n_internal:
    external: true
```

## 🔐 Sécurité

- ✅ Authentification Bearer Token obligatoire
- ✅ API Key stockée en variable d'environnement
- ✅ Communication sécurisée au sein du réseau Docker
- ✅ Logs d'audit de toutes les opérations
- ✅ Pas d'exposition publique par défaut

## 📝 Logs

Les logs sont disponibles :

```bash
# Logs Docker
docker logs proxmox-mcp

# Logs applicatifs
tail -f logs/proxmox-mcp.log
```

## 🔄 Commandes Utiles

```bash
# Redémarrer le serveur
docker compose restart

# Voir les logs en temps réel
docker compose logs -f

# Arrêter le serveur
docker compose down

# Reconstruire l'image
docker compose up -d --build

# Health check
curl http://localhost:8812/health
```

## 📚 Documentation

Pour plus de détails, consultez :
- `PROXMOX_MCP_COMPLETE.md` - Documentation complète
- `AUTHENTIFICATION.md` - Guide d'authentification Proxmox
- `QUICKSTART.md` - Guide de démarrage rapide

## 🤝 Contribution

Fork du projet original [ProxmoxMCP-Plus](https://github.com/RekklesNA/ProxmoxMCP-Plus)

## 📄 License

MIT

## 🙏 Crédits

- Projet original : [ProxmoxMCP-Plus](https://github.com/RekklesNA/ProxmoxMCP-Plus) by RekklesNA
- MCP Protocol : [Model Context Protocol](https://modelcontextprotocol.io)
- Proxmox API : [proxmoxer](https://github.com/proxmoxer/proxmoxer)
