@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM ============================================================================
REM Restauration PostgreSQL : annule/remplace la base aquademie_db
REM Fichier attendu : format custom pg_dump (-Fc), ex. aquademie_db.backup
REM
REM Usage :
REM   scripts\restore_aquademie_db.bat
REM   scripts\restore_aquademie_db.bat "C:\chemin\vers\aquademie_db.backup"
REM
REM Variables d'environnement optionnelles :
REM   PGPASSWORD      mot de passe du compte admin PostgreSQL
REM   PGADMIN         compte admin (defaut: postgres)
REM   DB_NAME         nom de la base (defaut: aquademie_db)
REM   DB_OWNER        proprietaire apres creation (defaut: aquademie_user)
REM   PGHOST          defaut: localhost
REM   PGPORT          defaut: 5432
REM ============================================================================

set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%..\"

if not defined PGADMIN set "PGADMIN=postgres"
if not defined DB_NAME set "DB_NAME=aquademie_db"
if not defined DB_OWNER set "DB_OWNER=aquademie_user"
if not defined PGHOST set "PGHOST=localhost"
if not defined PGPORT set "PGPORT=5432"

set "BACKUP_FILE=%~1"
if "%BACKUP_FILE%"=="" set "BACKUP_FILE=%PROJECT_DIR%aquademie_db.backup"

for %%I in ("%BACKUP_FILE%") do set "BACKUP_FILE=%%~fI"

echo.
echo === Restauration PostgreSQL (annule/remplace) ===
echo Base cible    : %DB_NAME%
echo Proprietaire  : %DB_OWNER%
echo Serveur       : %PGHOST%:%PGPORT%
echo Fichier       : %BACKUP_FILE%
echo Compte admin  : %PGADMIN%
echo.

if not exist "%BACKUP_FILE%" (
    echo [ERREUR] Fichier introuvable : %BACKUP_FILE%
    exit /b 1
)

where psql >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] psql introuvable. Ajoutez le dossier bin de PostgreSQL au PATH.
    echo Exemple : C:\Program Files\PostgreSQL\16\bin
    exit /b 1
)

where pg_restore >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] pg_restore introuvable. Ajoutez le dossier bin de PostgreSQL au PATH.
    exit /b 1
)

if not defined PGPASSWORD (
    set /p "PGPASSWORD=Mot de passe PostgreSQL pour %PGADMIN% : "
    echo.
)

set /p "CONFIRM=ATTENTION : la base '%DB_NAME%' sera SUPPRIMEE puis recreee. Continuer ? (O/N) : "
if /I not "%CONFIRM%"=="O" (
    echo Operation annulee.
    exit /b 0
)

echo.
echo [1/4] Fermeture des connexions actives sur %DB_NAME%...
psql -h %PGHOST% -p %PGPORT% -U %PGADMIN% -d postgres -v ON_ERROR_STOP=1 -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '%DB_NAME%' AND pid <> pg_backend_pid();"
if errorlevel 1 (
    echo [ERREUR] Impossible de fermer les connexions.
    exit /b 1
)

echo [2/4] Suppression de la base %DB_NAME%...
psql -h %PGHOST% -p %PGPORT% -U %PGADMIN% -d postgres -v ON_ERROR_STOP=1 -c "DROP DATABASE IF EXISTS %DB_NAME%;"
if errorlevel 1 (
    echo [ERREUR] Impossible de supprimer la base.
    exit /b 1
)

echo [3/4] Creation de la base %DB_NAME%...
psql -h %PGHOST% -p %PGPORT% -U %PGADMIN% -d postgres -v ON_ERROR_STOP=1 -c "CREATE DATABASE %DB_NAME% OWNER %DB_OWNER% ENCODING 'UTF8' TEMPLATE template0;"
if errorlevel 1 (
    echo [ERREUR] Impossible de creer la base.
    exit /b 1
)

echo [4/4] Restauration depuis %BACKUP_FILE%...
pg_restore -h %PGHOST% -p %PGPORT% -U %PGADMIN% -d %DB_NAME% --no-owner --role=%DB_OWNER% --verbose "%BACKUP_FILE%"
set "RESTORE_EXIT=%ERRORLEVEL%"

if %RESTORE_EXIT% GEQ 2 (
    echo.
    echo [ERREUR] pg_restore a echoue (code %RESTORE_EXIT%).
    exit /b %RESTORE_EXIT%
)

if %RESTORE_EXIT% EQU 1 (
    echo.
    echo [AVERTISSEMENT] Restauration terminee avec des avertissements (code 1).
    echo C'est souvent normal avec --no-owner / --role.
) else (
    echo.
    echo [OK] Restauration terminee avec succes.
)

echo.
echo Pensez a verifier l'application et, si besoin, lancer :
echo   python manage.py migrate
echo.

exit /b %RESTORE_EXIT%
