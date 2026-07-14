# Diagnostic des logs pour l'envoi de mail

## 📅 Contexte
Envoi de mail interrompu le **22:20** via l'écran "Communiquer avec les adhérents" en production sur serveur Linux.

## 🔍 Emplacements des logs à vérifier

### 1. Logs Gunicorn (Service Django)

Le service Gunicorn qui exécute l'application Django enregistre les erreurs dans les logs système.

```bash
# Voir les logs du service aquademie (dernières 100 lignes)
sudo journalctl -u aquademie -n 100 --no-pager

# Filtrer par date et heure (22:20 hier)
sudo journalctl -u aquademie --since "2025-01-XX 22:15:00" --until "2025-01-XX 22:30:00"

# Suivre les logs en temps réel
sudo journalctl -u aquademie -f

# Chercher les erreurs spécifiques
sudo journalctl -u aquademie | grep -i "error\|exception\|traceback\|mail\|email" | tail -50
```

**Emplacement du fichier de log** (si configuré différemment) :
- `/var/log/aquademie/gunicorn.log` (si configuré)
- `/var/www/aquademie/logs/` (si configuré)

### 2. Logs Nginx (Serveur Web)

Les erreurs HTTP et les timeouts peuvent être visibles dans les logs Nginx.

```bash
# Logs d'erreur Nginx
sudo tail -f /var/log/nginx/error.log

# Logs d'accès Nginx (pour voir la requête POST)
sudo grep "22:20" /var/log/nginx/access.log | grep "adherents_communiquer"

# Chercher les erreurs 502, 504, timeout
sudo grep -E "502|504|timeout|upstream" /var/log/nginx/error.log | tail -50
```

**Emplacements par défaut** :
- `/var/log/nginx/error.log`
- `/var/log/nginx/access.log`

### 3. Logs Django (si configurés)

Si Django logging est configuré dans `settings.py`, vérifiez les fichiers de log Django.

```bash
# Chercher un fichier de log Django (si configuré)
find /var/www/aquademie -name "*.log" -type f

# Logs Django typiques (si configurés)
# /var/www/aquademie/logs/django.log
# /var/www/aquademie/logs/error.log
```

**Note** : Actuellement, aucun système de logging Django n'est configuré dans `settings.py`. Il serait recommandé d'ajouter une configuration de logging pour faciliter le diagnostic.

### 4. Logs du serveur mail (SMTP)

Les erreurs de connexion SMTP ou les limites de taux peuvent être visibles dans les logs du serveur mail.

#### Si Postfix est utilisé localement :
```bash
# Logs Postfix
sudo tail -f /var/log/mail.log
sudo tail -f /var/log/mail.err

# Filtrer par date/heure
sudo grep "Jan XX 22:20" /var/log/mail.log
```

#### Si utilisation directe de SMTP externe (OVH) :
Les erreurs SMTP seront dans les logs Django/Gunicorn, car la connexion se fait directement depuis l'application.

### 5. Logs système (syslog)

Les erreurs système générales peuvent être visibles dans syslog.

```bash
# Logs système généraux
sudo tail -f /var/log/syslog

# Filtrer par date/heure
sudo grep "Jan XX 22:20" /var/log/syslog | grep -i "aquademie\|python\|gunicorn"
```

### 6. Logs de la base de données (PostgreSQL)

Si l'application utilise PostgreSQL, vérifiez les logs de la base de données.

```bash
# Logs PostgreSQL
sudo tail -f /var/log/postgresql/postgresql-*.log

# Chercher les erreurs de connexion ou timeout
sudo grep -i "error\|timeout\|connection" /var/log/postgresql/postgresql-*.log | tail -50
```

## 🔎 Commandes de diagnostic rapide

### Commande complète pour analyser l'incident
```bash
# Créer un rapport complet pour l'heure de l'incident
INCIDENT_DATE="2025-01-XX"  # Remplacer XX par la date
INCIDENT_TIME="22:20"

echo "=== LOGS GUNICORN ===" > /tmp/diagnostic_mail.txt
sudo journalctl -u aquademie --since "$INCIDENT_DATE $INCIDENT_TIME:00" --until "$INCIDENT_DATE 22:30:00" >> /tmp/diagnostic_mail.txt

echo -e "\n=== LOGS NGINX ERROR ===" >> /tmp/diagnostic_mail.txt
sudo grep "$INCIDENT_DATE.*22:2" /var/log/nginx/error.log >> /tmp/diagnostic_mail.txt

echo -e "\n=== LOGS NGINX ACCESS ===" >> /tmp/diagnostic_mail.txt
sudo grep "$INCIDENT_DATE.*22:2" /var/log/nginx/access.log | grep -i "adherents\|communiquer" >> /tmp/diagnostic_mail.txt

echo -e "\n=== LOGS SYSTÈME ===" >> /tmp/diagnostic_mail.txt
sudo grep "$INCIDENT_DATE.*22:2" /var/log/syslog | grep -i "aquademie\|python\|gunicorn" >> /tmp/diagnostic_mail.txt

cat /tmp/diagnostic_mail.txt
```

## 🐛 Causes possibles de l'interruption

### 1. Timeout HTTP
- **Symptôme** : Requête qui prend trop de temps (> 120 secondes par défaut)
- **Logs à vérifier** : Nginx error.log, Gunicorn logs
- **Solution** : Augmenter le timeout dans Nginx/Gunicorn ou utiliser une tâche asynchrone

### 2. Limite de taux SMTP
- **Symptôme** : Erreur "Too many emails" ou "Rate limit exceeded"
- **Logs à vérifier** : Gunicorn logs, Django logs
- **Solution** : Réduire la taille des lots ou augmenter le délai entre les lots

### 3. Erreur de connexion SMTP
- **Symptôme** : Erreur de connexion au serveur SMTP (ssl0.ovh.net)
- **Logs à vérifier** : Gunicorn logs, Django logs
- **Solution** : Vérifier la connexion réseau, les credentials SMTP

### 4. Mémoire insuffisante
- **Symptôme** : Processus tué (OOM Killer)
- **Logs à vérifier** : syslog, dmesg
- **Solution** : Vérifier `dmesg | grep -i "killed\|oom"`

### 5. Exception Python non gérée
- **Symptôme** : Traceback dans les logs
- **Logs à vérifier** : Gunicorn logs
- **Solution** : Corriger le code pour gérer les exceptions

## 📝 Code actuel - Points d'attention

Dans `gestion/views.py` (lignes 2862-2879), l'envoi de mail se fait en lots de 10 avec une pause de 3 secondes, mais **il n'y a pas de gestion d'erreur** dans la boucle. Si une exception se produit, l'envoi s'arrête.

```python
# Envoi par lots de 10 avec pause
batch_size = 10
for i in range(0, len(destinataires), batch_size):
    batch = destinataires[i:i+batch_size]
    email = EmailMessage(...)
    email.send()  # ⚠️ Pas de try/except ici
    if (i + batch_size) < len(destinataires):
        time.sleep(3)
```

## ✅ Recommandations

1. **Ajouter une gestion d'erreur** dans la boucle d'envoi
2. **Configurer le logging Django** pour capturer les erreurs d'envoi
3. **Utiliser une tâche asynchrone** (Celery) pour les envois de masse
4. **Ajouter des logs détaillés** pour suivre la progression de l'envoi

## 🔧 Commandes utiles pour le monitoring

```bash
# Vérifier l'état du service
sudo systemctl status aquademie

# Vérifier l'utilisation mémoire
free -h

# Vérifier l'espace disque
df -h

# Vérifier les processus Python
ps aux | grep python | grep gunicorn

# Vérifier les connexions réseau
netstat -an | grep :465  # Port SMTP SSL
```

---

**Date de création** : $(date)
**Application** : Aquadémie Paris Plongée
**Environnement** : Production Linux

