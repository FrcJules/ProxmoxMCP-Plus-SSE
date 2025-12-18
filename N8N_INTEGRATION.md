# Integration n8n avec ProxmoxMCP

## Vue d ensemble

ProxmoxMCP expose maintenant deux interfaces :
1. **API REST** (port 8811) : Pour utilisation generale, API OpenAPI avec authentification
2. **Serveur MCP SSE** (port 8812) : Pour integration avec n8n et autres clients MCP

## Configuration n8n

### Prerequis

Assurez-vous que n8n est installe avec le support MCP. Si vous utilisez n8n self-hosted, definissez la variable d environnement :

```bash
N8N_COMMUNITY_PACKAGES_ALLOW_TOOL_USAGE=true
```

### Etapes de configuration

#### 1. Acces a n8n

Connectez-vous a votre instance n8n

#### 2. Creer un workflow avec MCP

1. Creez un nouveau workflow
2. Ajoutez un noeud **Chat Trigger** (ou tout autre trigger)
3. Ajoutez un noeud **AI Agent**
4. Connectez le trigger a l AI Agent

#### 3. Ajouter le noeud MCP Client Tool

1. Dans l AI Agent, cliquez sur "Add Tool"
2. Selectionnez **MCP Client Tool**
3. Configurez les parametres suivants :

**Configuration SSE Endpoint :**
```
SSE Endpoint: http://192.168.1.127:8812/proxmox/mcp
```

**Authentication :**
```
Authentication Method: None
```

**Important :** Le serveur SSE de ProxmoxMCP n utilise actuellement pas d authentification. L authentification est geree par l API REST sur le port 8811.

#### 4. Selectionner les outils

Une fois connecte, n8n affichera la liste des outils disponibles de ProxmoxMCP :

- get_nodes
- get_node_status
- get_vms
- create_vm
- start_vm
- stop_vm
- shutdown_vm
- reset_vm
- delete_vm
- execute_vm_command
- get_containers
- start_container
- stop_container
- restart_container
- update_container_resources
- get_storage
- get_cluster_status

Selectionnez les outils que vous souhaitez utiliser dans votre workflow.

#### 5. Tester la connexion

1. Executez le workflow
2. Envoyez un message test comme "Liste les VMs Proxmox"
3. L AI agent devrait utiliser le tool get_vms pour repondre

## URLs de connexion

### Pour n8n sur le meme serveur (localhost)

```
SSE Endpoint: http://localhost:8812/proxmox/mcp
```

### Pour n8n sur un autre serveur dans le reseau local

```
SSE Endpoint: http://192.168.1.127:8812/proxmox/mcp
```

### Pour n8n en dehors du reseau local

Si n8n est heberge ailleurs (ex: n8n Cloud), vous devez :

1. **Option 1 : Reverse Proxy avec SSL**
   - Configurer un reverse proxy (Nginx/Traefik) avec certificat SSL
   - Exposer le port 8812 de maniere securisee
   - Exemple : https://votre-domaine.com/proxmox-mcp/sse

2. **Option 2 : Tunnel (ngrok, cloudflare tunnel)**
   - Creer un tunnel vers le port 8812
   - Utiliser l URL du tunnel dans n8n

## Exemple de configuration n8n

### Configuration minimale

```json
{
  "sseEndpoint": "http://192.168.1.127:8812/proxmox/mcp",
  "authentication": "none"
}
```

### Exemple de workflow n8n

```
[Chat Trigger] --> [AI Agent avec MCP Client Tool] --> [Reponse]
```

Prompt exemple :
- "Liste toutes les VMs sur Proxmox"
- "Demarre la VM avec l ID 103"
- "Montre moi le statut du node pve01"
- "Liste tous les containers LXC"

## Verification de la connexion

### Depuis n8n

Une fois la configuration sauvegardee, n8n devrait automatiquement se connecter et afficher les outils disponibles.

### Tester manuellement l endpoint SSE

```bash
# Test simple (devrait rester en attente, c est normal pour SSE)
curl -N http://192.168.1.127:8812/proxmox/mcp
```

### Verifier les logs du serveur

```bash
cd /home/rateur42/proxmoxMCP
docker compose logs -f proxmox-mcp-sse
```

## Architecture

```
n8n (Client MCP)
    |
    | SSE Connection
    v
http://192.168.1.127:8812/proxmox/mcp
    |
    | FastMCP SSE Server
    v
ProxmoxMCP Tools
    |
    | Proxmoxer API
    v
Proxmox VE (192.168.1.81:8006)
```

## Ports utilises

- **8811** : API REST avec mcpo (authentification par API key)
- **8812** : Serveur MCP SSE (pour n8n et clients MCP)

## Troubleshooting

### n8n ne peut pas se connecter

1. Verifier que le container SSE est en cours d execution :
   ```bash
   docker compose ps
   ```

2. Verifier les logs :
   ```bash
   docker compose logs proxmox-mcp-sse
   ```

3. Tester la connexion depuis le serveur :
   ```bash
   curl -N http://localhost:8812/proxmox/mcp
   ```

4. Verifier que le port 8812 est accessible depuis n8n :
   ```bash
   # Depuis le serveur n8n
   curl -N http://192.168.1.127:8812/proxmox/mcp
   ```

### Erreur "Connection timeout"

- Verifier le firewall sur le serveur Proxmox MCP
- Autoriser le port 8812 :
  ```bash
  sudo ufw allow 8812
  ```

### Les outils n apparaissent pas dans n8n

- Verifier que le SSE endpoint est correct
- Consulter les logs du container SSE
- Redemarre r le workflow n8n

## Securite

### Important

Le serveur SSE (port 8812) n a actuellement PAS d authentification. Pour securiser :

#### Option 1 : Firewall (Recommande)

Autoriser uniquement l IP de votre serveur n8n :

```bash
# Bloquer tout acces au port 8812
sudo ufw deny 8812

# Autoriser uniquement l IP de n8n
sudo ufw allow from <IP_N8N> to any port 8812
```

#### Option 2 : Reseau interne Docker

Si n8n et ProxmoxMCP sont sur le meme serveur, utilisez un reseau Docker interne.

#### Option 3 : Reverse Proxy avec authentification

Configurez Nginx/Traefik avec authentification basique devant le port 8812.

## Ressources supplementaires

- Documentation n8n MCP : https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.toolmcp/
- Model Context Protocol : https://modelcontextprotocol.io/
- ProxmoxMCP GitHub : https://github.com/RekklesNA/ProxmoxMCP-Plus

## Support

Pour tout probleme :
1. Consulter les logs : `docker compose logs proxmox-mcp-sse`
2. Verifier la documentation n8n
3. Verifier que Proxmox est accessible (192.168.1.81:8006)
