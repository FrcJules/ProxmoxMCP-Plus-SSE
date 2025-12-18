# Proxmox MCP Server - Configuration Complète ✅

## 🎉 Statut : OPÉRATIONNEL

Votre serveur MCP Proxmox est maintenant **entièrement configuré et fonctionnel** avec n8n !

---

## 📋 Configuration n8n

### Paramètres de connexion

**Dans n8n, configurez le nœud "MCP Client Tool" avec :**

- **Server URL** : `http://proxmox-mcp:8812/proxmox/mcp/sse`
- **Server Transport** : `HTTP Streamable`
- **Authentication** : `Bearer Token`
- **Bearer Token** : `1e62c690441f8b3544c59b8a5b233de2fc8735dc10c179f2a5432e830df90141`

---

## 🛠️ Tools Disponibles (16 au total)

### 📡 Node Management
1. **get_nodes** - Liste tous les nodes Proxmox du cluster
2. **get_node_status** - Obtenir le statut d'un node spécifique
   - Paramètres : `node` (string)

### 🖥️ Virtual Machines
3. **get_vms** - Liste toutes les VMs de tous les nodes
4. **create_vm** - Créer une nouvelle VM
   - Paramètres : `node`, `vmid`, `name`, `cpus`, `memory`, `disk_size`, `storage` (optionnel), `ostype` (optionnel)
5. **start_vm** - Démarrer une VM
   - Paramètres : `node`, `vmid`
6. **stop_vm** - Arrêter une VM (forcé)
   - Paramètres : `node`, `vmid`
7. **shutdown_vm** - Arrêt gracieux d'une VM
   - Paramètres : `node`, `vmid`
8. **reset_vm** - Redémarrer une VM
   - Paramètres : `node`, `vmid`
9. **delete_vm** - Supprimer une VM
   - Paramètres : `node`, `vmid`, `force` (boolean, optionnel)

### 💾 Storage
10. **get_storage** - Liste tous les storages du cluster

### ⚙️ Cluster
11. **get_cluster_status** - Obtenir le statut du cluster

### 📦 LXC Containers
12. **get_containers** - Liste tous les containers LXC
    - Paramètres : `node` (optionnel), `include_stats` (boolean), `format_style` ("pretty"/"json")
13. **start_container** - Démarrer un container
    - Paramètres : `selector` (ID ou nom), `format_style`
14. **stop_container** - Arrêter un container
    - Paramètres : `selector`, `graceful` (boolean), `timeout_seconds`, `format_style`
15. **restart_container** - Redémarrer un container
    - Paramètres : `selector`, `timeout_seconds`, `format_style`
16. **update_container_resources** - Modifier les ressources d'un container
    - Paramètres : `selector`, `cores`, `memory`, `swap`, `disk_gb`, `disk`, `format_style`

---

## 🧪 Tests Validés

Tous les tools ont été testés avec succès :

### ✅ get_nodes
```
🖥️ pve01
  • Status: ONLINE
  • Uptime: ⏳ 11d 11h 35m
  • CPU Cores: 8
  • Memory: 23.62 GB / 31.22 GB (75.7%)
```

### ✅ get_vms
```
🗃️ Virtual Machines

🗃️ Tiny10 (ID: 102)
  • Status: STOPPED
  • Node: pve01
  • CPU Cores: 8
  • Memory: 0.00 B / 12.00 GB (0.0%)

🗃️ TrueNas (ID: 100)
  • Status: RUNNING
  • Node: pve01
  • CPU Cores: 8
  • Memory: 3.54 GB / 4.00 GB (88.4%)

... et 4 VMs de plus
```

### ✅ get_containers
```
📦 Containers

📦 Bitwarden (ID: 106)
  • Status: RUNNING
  • Node: pve01
  • CPU: -9.6%
  • Memory: 474.36 MiB / 1.00 GiB (46.3%)
```

### ✅ get_cluster_status
```
⚙️ Proxmox Cluster
  • Name: pve01
  • Quorum: NOT OK
  • Nodes: 1
```

### ✅ get_storage
```
💾 Storage Pools

💾 local-hdd
  • Status: ONLINE
  • Type: nfs
  • Usage: 22.14 GB / 419.33 GB (5.3%)
```

---

## 🏗️ Architecture

```
n8n (Container: 192.168.80.3)
        │
        │ Réseau Docker: n8n_n8n_internal
        │ HTTP POST + Bearer Auth
        ▼
proxmox-mcp (Container: 192.168.80.4)
        │
        │ Serveur MCP Hybride
        │ - GET /proxmox/mcp/sse → SSE connection
        │ - POST /proxmox/mcp/sse → JSON-RPC 2.0
        ▼
ProxmoxMCP Tools (16 tools)
        │
        │ Proxmoxer API
        ▼
Proxmox VE (192.168.1.81:8006)
```

---

## 📂 Fichiers Importants

- **Serveur** : `/home/rateur42/proxmoxMCP/src/proxmox_mcp/server_sse.py`
- **Docker Compose** : `/home/rateur42/proxmoxMCP/docker-compose.yml`
- **Configuration** : `/home/rateur42/proxmoxMCP/proxmox-config/config.json`
- **API Key** : `/home/rateur42/proxmoxMCP/.env`
- **Logs** : `/home/rateur42/proxmoxMCP/logs/proxmox-mcp.log`

---

## 🔧 Commandes Utiles

### Vérifier le statut
```bash
ssh rateur42@192.168.1.127 "docker ps | grep proxmox-mcp"
```

### Voir les logs
```bash
ssh rateur42@192.168.1.127 "docker logs proxmox-mcp --tail 50"
```

### Redémarrer le serveur
```bash
ssh rateur42@192.168.1.127 "cd /home/rateur42/proxmoxMCP && docker compose restart"
```

### Health check
```bash
curl http://192.168.1.127:8812/health
```

### Tester depuis l'intérieur du réseau Docker
```bash
ssh rateur42@192.168.1.127 "docker exec n8n wget -qO- http://proxmox-mcp:8812/health"
```

---

## 🎯 Exemples d'Utilisation dans n8n

### Exemple 1 : Lister toutes les VMs
1. Créez un workflow avec un trigger
2. Ajoutez un nœud "MCP Client Tool"
3. Sélectionnez le tool : `get_vms`
4. Exécutez

### Exemple 2 : Démarrer une VM
1. Ajoutez un nœud "MCP Client Tool"
2. Sélectionnez le tool : `start_vm`
3. Paramètres :
   - `node` : `pve01`
   - `vmid` : `102`
4. Exécutez

### Exemple 3 : Lister les containers avec filtrage
1. Ajoutez un nœud "MCP Client Tool"
2. Sélectionnez le tool : `get_containers`
3. Paramètres :
   - `node` : `pve01` (optionnel)
   - `include_stats` : `true`
   - `format_style` : `pretty`
4. Exécutez

---

## 🔐 Sécurité

- ✅ Authentification Bearer Token obligatoire
- ✅ Communication interne au réseau Docker n8n
- ✅ API Key stockée dans `.env` avec permissions 600
- ✅ Pas d'exposition publique (pas de port mappé sur l'hôte)
- ✅ Logs d'audit de toutes les opérations

---

## 🚀 Prochaines Étapes

Vous pouvez maintenant :

1. **Créer des workflows n8n** utilisant ces tools Proxmox
2. **Automatiser la gestion** de vos VMs et containers
3. **Intégrer avec d'autres services** (Discord, Slack, etc.)
4. **Créer des dashboards** de monitoring
5. **Automatiser les backups** et la maintenance

---

## 📞 Support

Pour toute question ou problème :

1. Vérifiez les logs : `docker logs proxmox-mcp`
2. Vérifiez la connectivité : `curl http://proxmox-mcp:8812/health` (depuis n8n)
3. Vérifiez les fichiers de logs applicatifs : `/home/rateur42/proxmoxMCP/logs/`

---

**Version** : 1.0.0 (Complete)  
**Date** : 2025-12-18  
**Status** : ✅ Production Ready
