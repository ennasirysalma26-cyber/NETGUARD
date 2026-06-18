# NetAdmin API — FastAPI

API REST complète pour la gestion des équipements réseau.

## Stack technique

| Composant | Technologie |
|-----------|-------------|
| Framework | FastAPI 0.115 |
| ORM       | SQLAlchemy 2 (async) |
| Base de données | PostgreSQL 16 |
| Cache / Queue | Redis 7 |
| Auth | JWT (python-jose + passlib) |
| Ping ICMP | icmplib |
| SNMP | pysnmp |
| Conteneurs | Docker + Docker Compose |

## Structure du projet

```
netadmin/
├── app/
│   ├── main.py                  # Point d'entrée FastAPI
│   ├── core/
│   │   ├── database.py          # Moteur SQLAlchemy async
│   │   ├── security.py          # JWT, hachage, dépendances auth
│   │   └── websocket.py         # Gestionnaire WebSocket
│   ├── models/
│   │   └── models.py            # Tous les modèles ORM
│   ├── schemas/
│   │   └── schemas.py           # Schémas Pydantic (validation)
│   ├── routers/
│   │   ├── auth.py              # POST /auth/login, /refresh, /logout
│   │   ├── devices.py           # CRUD + import/export CSV
│   │   ├── probe.py             # Ping, SNMP, WebSocket
│   │   ├── interventions.py     # Historique des interventions
│   │   ├── alerts.py            # Alertes + acquittement
│   │   └── topology.py          # Graphe réseau
│   └── services/
│       └── probe_service.py     # Moteur ICMP + SNMP
├── migrations/
│   └── versions/001_initial.py  # Migration Alembic initiale
├── tests/
│   └── test_api.py              # Tests pytest-asyncio
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## Démarrage rapide

### 1. Variables d'environnement

Créer un fichier `.env` à la racine :

```env
DATABASE_URL=postgresql+asyncpg://netadmin:secret@localhost:5432/netadmin
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=votre-cle-secrete-longue-et-aleatoire
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7
```

### 2. Démarrage avec Docker

```bash
docker-compose up -d
```

L'API est disponible sur : http://localhost:8000
Documentation Swagger : http://localhost:8000/docs

### 3. Démarrage sans Docker

```bash
# Installer les dépendances
pip install -r requirements.txt

# Lancer les migrations
alembic upgrade head

# Démarrer l'API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Lancer les tests

```bash
pip install aiosqlite pytest-asyncio
pytest tests/ -v
```

## Endpoints principaux

| Méthode | Route | Description |
|---------|-------|-------------|
| POST | /api/v1/auth/login | Connexion |
| GET  | /api/v1/devices | Liste équipements |
| POST | /api/v1/devices | Créer un équipement |
| PUT  | /api/v1/devices/{id} | Modifier |
| DELETE | /api/v1/devices/{id} | Supprimer |
| POST | /api/v1/devices/import | Import CSV |
| GET  | /api/v1/devices/export | Export CSV |
| POST | /api/v1/probe/ping/{id} | Ping ICMP |
| POST | /api/v1/probe/snmp/{id} | Collecte SNMP |
| GET  | /api/v1/probe/history/{id} | Historique RTT |
| GET  | /api/v1/probe/scan/status | État global |
| GET  | /api/v1/interventions | Historique |
| GET  | /api/v1/alerts | Alertes actives |
| PUT  | /api/v1/alerts/{id}/acknowledge | Acquitter |
| GET  | /api/v1/topology | Graphe réseau |
| WS   | /api/v1/probe/ws/probe | Sondes temps réel |
| WS   | /api/v1/probe/ws/alerts | Alertes temps réel |

## Rôles et permissions

| Rôle | Lecture | Création/Modif | Suppression |
|------|---------|----------------|-------------|
| lecteur | ✓ | ✗ | ✗ |
| technicien | ✓ | ✓ | ✗ |
| admin | ✓ | ✓ | ✓ |

## Note ICMP (permissions)

Le ping ICMP nécessite des sockets raw (root ou CAP_NET_RAW).
Le service inclut un fallback TCP automatique si les permissions sont insuffisantes.

En production avec Docker, la permission est activée via :
```yaml
cap_add:
  - NET_RAW
```
