# Runbook — Décommissionnement du Backend Laravel

**Version** : 1.0  
**Dernière mise à jour** : 2025-05-26  
**Propriétaire** : Équipe DevOps  
**Criticité** : Haute — Opération irréversible sans rollback explicite

---

## Pré-requis

### Accès requis

| Accès | Détail | Responsable |
|---|---|---|
| SSH serveur production | `ssh deploy@api.clinique.app` | DevOps |
| Accès Docker | `docker ps`, `docker stop` | DevOps |
| Accès Nginx | `/etc/nginx/sites-available/` avec sudo | DevOps |
| Accès MySQL production | Lecture + dump | DBA |
| Accès Prometheus | `http://prometheus:9090` | DevOps |
| Accès Slack | `#ops-prod`, `#incidents` | Toute l'équipe |
| Accès PagerDuty | Escalade incident | On-call engineer |

### Contacts équipe

| Rôle | Nom | Slack | Téléphone |
|---|---|---|---|
| Lead DevOps | À compléter | `@devops-lead` | À compléter |
| Lead Backend Python | À compléter | `@backend-lead` | À compléter |
| DBA | À compléter | `@dba` | À compléter |
| Product Owner | À compléter | `@po` | À compléter |
| Astreinte On-call | Rotation PagerDuty | — | PagerDuty |

### Outils nécessaires sur le poste

```bash
curl --version      # >= 7.x
docker --version    # >= 24.x
nginx -v            # >= 1.24.x
python3 --version   # >= 3.12
```

---

## Critères de déclenchement

Le décommissionnement ne doit être lancé que si **toutes** les conditions suivantes sont réunies :

### Critères techniques

- [ ] **100% des endpoints migrés** : la liste complète des 290 endpoints Laravel est couverte par le backend Python (vérifier le fichier `CHANGELOG.md`)
- [ ] **Tests API** : couverture 100% des endpoints critiques (appointments, billing, auth) par des tests automatisés passants
- [ ] **Performance validée** : P99 < 200 ms sous 200 utilisateurs simultanés pendant 5 minutes (rapport Locust disponible)
- [ ] **Taux d'erreur** : < 0,1% sur les 7 derniers jours en production (dashboard Prometheus)
- [ ] **Monitoring** : 7 jours consécutifs sans incident P1 ou P2 lié au backend Python

### Critères métier

- [ ] **UAT signé** : validation fonctionnelle par le Product Owner sur au minimum 3 cliniques pilotes
- [ ] **Communication clients** : email envoyé aux administrateurs de cliniques 72h avant (voir section Communication)
- [ ] **Fenêtre de maintenance** : créneau approuvé par le PO (hors heures de pointe : 22h-4h, de préférence un mardi ou mercredi)

---

## Étapes détaillées

### Préparation (J-3 à J-1)

#### J-3 : Validation finale

```bash
# 1. Vérifier la couverture des endpoints
cd /home/centenier/centenier/mobile_projects/gestion_clinique/backend\ and\ front/python-api
python scripts/verify_migration.py

# 2. Lancer un test de charge complet (10 min)
locust --headless --users 200 --spawn-rate 10 \
       --host https://staging-api.clinique.app \
       --run-time 10m \
       --csv results/pre_decommission_$(date +%Y%m%d) \
       -f tests/load/locustfile.py

# 3. Vérifier le rapport
cat results/pre_decommission_*.csv | head -5
```

#### J-1 : Backup de sécurité

```bash
# Backup manuel complet (en plus du backup automatisé)
bash scripts/backup_laravel.sh production

# Vérifier que le backup est présent
ls -lh /backups/laravel/$(date +%Y%m%d)*/

# Tester la restauration du dump SQL sur un environnement de test
mysql -h test-db -u root -p clinique_test < /backups/laravel/.../database_*.sql
```

#### J-1 : Notification équipe

Poster dans `#ops-prod` :
```
[DECOMMISSIONNEMENT LARAVEL] Demain XX/XX à 22h00
- Durée estimée : 30-45 minutes
- Impact : aucun (migration progressive déjà à 100%)
- On-call : @nom-engineer
- Rollback disponible : bash scripts/rollback_to_laravel.sh production
```

---

### Décommissionnement (Jour J)

#### Étape 0 : Vérifications pré-opération (22h00)

```bash
# Vérifier que le backend Python répond
curl -s https://api.clinique.app/health | python3 -m json.tool

# Vérifier les métriques Prometheus (taux d'erreur < 0.1%)
curl -s "http://prometheus:9090/api/v1/query?query=rate(http_requests_total{status=~'5..'}[5m])"

# Vérifier qu'aucun déploiement n'est en cours
docker ps | grep python-api
```

Si un problème est détecté : **ne pas continuer**, reporter l'opération.

#### Étape 1 : Lancer le script de décommissionnement (22h10)

```bash
# Connexion au serveur
ssh deploy@api.clinique.app

# Se positionner dans le répertoire du projet
cd /opt/python-api

# Lancer le décommissionnement (mode production)
bash scripts/decommission_laravel.sh production
```

Le script effectue automatiquement :
1. Vérification santé Python (/health)
2. Backup final Laravel (code + base + storage)
3. Vérification taux d'erreur Prometheus
4. Basculement Nginx → Python 100%
5. Arrêt gracieux du conteneur Laravel (30s timeout)
6. Vérification finale (/health)

#### Étape 2 : Surveillance post-décommissionnement (22h30 – 23h30)

```bash
# Surveiller les logs Python en temps réel
docker logs -f python-api --tail=100

# Surveiller Nginx
tail -f /var/log/nginx/api_error.log

# Dashboard Prometheus (taux d'erreur, latences)
# Ouvrir : http://prometheus:9090/graph
# Requête : rate(http_requests_total[1m])
```

**Seuils d'alerte déclenchant un rollback** :
- Taux d'erreur 5xx > 1% sur 5 minutes
- Latence P99 > 500 ms sur 5 minutes
- Health check `/health` répond != 200

#### Étape 3 : Validation finale (23h30)

```bash
# Test fonctionnel rapide des endpoints critiques
curl -s https://api.clinique.app/health
curl -s https://api.clinique.app/api/countries | python3 -m json.tool
curl -s -X POST https://api.clinique.app/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"test@test.com","password":"test"}' | python3 -m json.tool
```

---

## Procédure de rollback

### Rollback automatisé (< 30 secondes)

```bash
bash scripts/rollback_to_laravel.sh production
```

### Rollback manuel (si le script échoue)

```bash
# 1. Restaurer la dernière config Nginx Laravel
LATEST=$(ls -t /etc/nginx/backup/clinique.conf.* | head -1)
cp "$LATEST" /etc/nginx/sites-available/clinique.conf
nginx -t && nginx -s reload

# 2. Redémarrer Laravel
docker start laravel-app || docker-compose up -d laravel

# 3. Vérifier
sleep 10
curl -s https://api.clinique.app/health
```

### Après un rollback

1. Ouvrir un incident P1 sur PagerDuty
2. Poster dans `#incidents` : cause du rollback, état du système, ETA de correction
3. Ne pas relancer le décommissionnement sans analyse post-mortem complète

---

## Plan de communication

### Communication préventive (J-3)

**Email clients** (administrateurs de cliniques) :
```
Objet : Maintenance technique programmée — XX/XX à 22h00

Mesdames, Messieurs,

Nous effectuerons une maintenance technique le XX/XX de 22h00 à 23h00.
L'application restera disponible pendant toute la durée de l'opération.
Aucune action de votre part n'est requise.

L'équipe technique de Clinique App
```

### Communication équipe (J-1)

Slack `#ops-prod` : notification de l'opération avec contacts d'astreinte.

### Communication pendant l'opération

Poster une mise à jour dans `#ops-prod` à chaque étape complétée.

### Communication post-opération

```
[DECOMMISSIONNEMENT LARAVEL] TERMINE avec succes
- Debut : 22h10
- Fin : 22h38
- Incidents : aucun
- Prochaine etape : monitoring 7 jours, puis suppression des backups Laravel dans 30 jours
```

---

## Checklist post-décommissionnement

### Immédiat (dans les 24h)

- [ ] Vérifier les métriques Prometheus pendant 1h après l'opération
- [ ] Vérifier que les alertes Prometheus/Grafana ne se déclenchent pas
- [ ] Tester manuellement les 10 endpoints les plus critiques
- [ ] Confirmer que les cliniques pilotes ne signalent pas d'anomalie
- [ ] Archiver les logs du décommissionnement dans Confluence / Notion

### Semaine 1

- [ ] Monitoring quotidien des métriques (taux erreur, latence, CPU/RAM)
- [ ] S'assurer que le cron de backup Python est actif
- [ ] Vérifier que les webhooks Stripe/PayPal continuent de fonctionner
- [ ] Organiser un post-mortem de l'opération (réussite ou non)

### Dans les 30 jours

- [ ] Supprimer les images Docker Laravel des registries (conserver le code source archivé)
- [ ] Mettre à jour la documentation d'architecture
- [ ] Supprimer les variables d'environnement Laravel du vault de secrets
- [ ] Fermer les tickets de migration dans le backlog

### Dans les 90 jours

- [ ] Évaluer si les backups Laravel (code + SQL) peuvent être archivés sur stockage froid
- [ ] Résilier les licences/services liés à Laravel si applicable
- [ ] Mettre à jour les contrats de support/hébergement
