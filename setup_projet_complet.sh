#!/bin/bash
# Script de configuration complète du projet Clinique N
# Usage: ./setup_projet_complet.sh

set -e

# Couleurs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                                                           ║"
echo "║        🏥  CLINIQUE N - Configuration Complète  🏥        ║"
echo "║                                                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

# Vérifier les prérequis
echo -e "${YELLOW}📋 Vérification des prérequis...${NC}"
echo ""

# Git
if command -v git &> /dev/null; then
    echo -e "${GREEN}✓${NC} Git installé: $(git --version)"
else
    echo -e "${RED}✗${NC} Git n'est pas installé"
    exit 1
fi

# Docker
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✓${NC} Docker installé: $(docker --version)"
else
    echo -e "${RED}✗${NC} Docker n'est pas installé"
    exit 1
fi

# Docker Compose
if command -v docker compose &> /dev/null; then
    echo -e "${GREEN}✓${NC} Docker Compose installé"
else
    echo -e "${RED}✗${NC} Docker Compose n'est pas installé"
    exit 1
fi

# Node.js
if command -v node &> /dev/null; then
    echo -e "${GREEN}✓${NC} Node.js installé: $(node --version)"
else
    echo -e "${YELLOW}⚠${NC} Node.js n'est pas installé (requis pour frontend)"
fi

# pnpm
if command -v pnpm &> /dev/null; then
    echo -e "${GREEN}✓${NC} pnpm installé: $(pnpm --version)"
else
    echo -e "${YELLOW}⚠${NC} pnpm n'est pas installé (requis pour frontend)"
fi

# Flutter
if command -v flutter &> /dev/null; then
    echo -e "${GREEN}✓${NC} Flutter installé: $(flutter --version | head -1)"
else
    echo -e "${YELLOW}⚠${NC} Flutter n'est pas installé (requis pour mobile)"
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Créer le dossier de travail
WORKSPACE_DIR="$HOME/clinique-n"
echo -e "${YELLOW}📁 Création du workspace: $WORKSPACE_DIR${NC}"
mkdir -p "$WORKSPACE_DIR"
cd "$WORKSPACE_DIR"
echo -e "${GREEN}✓${NC} Workspace créé"
echo ""

# Cloner les dépôts
echo -e "${YELLOW}📦 Clonage des dépôts GitHub...${NC}"
echo ""

# Backend
if [ ! -d "clinique-n-api" ]; then
    echo -e "${BLUE}🔧 Clonage du Backend (API)...${NC}"
    git clone https://github.com/roland171993/clinique-n-api.git
    echo -e "${GREEN}✓${NC} Backend cloné"
else
    echo -e "${GREEN}✓${NC} Backend déjà présent"
fi

# Frontend
if [ ! -d "clinique-n-frontend" ]; then
    echo -e "${BLUE}🎨 Clonage du Frontend (React)...${NC}"
    git clone https://github.com/roland171993/clinique-n-frontend.git
    echo -e "${GREEN}✓${NC} Frontend cloné"
else
    echo -e "${GREEN}✓${NC} Frontend déjà présent"
fi

# Mobile
if [ ! -d "clinique-n-mobile" ]; then
    echo -e "${BLUE}📱 Clonage du Mobile (Flutter)...${NC}"
    git clone https://github.com/roland171993/clinique-n-mobile.git
    echo -e "${GREEN}✓${NC} Mobile cloné"
else
    echo -e "${GREEN}✓${NC} Mobile déjà présent"
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Configuration Backend
echo -e "${YELLOW}🔧 Configuration du Backend...${NC}"
cd "$WORKSPACE_DIR/clinique-n-api"

if [ ! -f ".env" ]; then
    echo -e "${BLUE}Copie de .env.example vers .env${NC}"
    cp .env.example .env
    echo -e "${GREEN}✓${NC} Fichier .env créé"
    echo -e "${YELLOW}⚠ N'oubliez pas de modifier les variables dans .env${NC}"
else
    echo -e "${GREEN}✓${NC} Fichier .env existe"
fi

echo ""

# Configuration Frontend
if command -v pnpm &> /dev/null; then
    echo -e "${YELLOW}🎨 Configuration du Frontend...${NC}"
    cd "$WORKSPACE_DIR/clinique-n-frontend"
    
    if [ ! -f ".env" ]; then
        echo -e "${BLUE}Copie de .env.example vers .env${NC}"
        cp .env.example .env 2>/dev/null || echo "# Configuration Frontend" > .env
        echo -e "${GREEN}✓${NC} Fichier .env créé"
    else
        echo -e "${GREEN}✓${NC} Fichier .env existe"
    fi
    
    echo -e "${BLUE}Installation des dépendances pnpm...${NC}"
    pnpm install
    echo -e "${GREEN}✓${NC} Dépendances installées"
else
    echo -e "${YELLOW}⚠ pnpm non installé, configuration Frontend ignorée${NC}"
fi

echo ""

# Configuration Mobile
if command -v flutter &> /dev/null; then
    echo -e "${YELLOW}📱 Configuration du Mobile...${NC}"
    cd "$WORKSPACE_DIR/clinique-n-mobile"
    
    if [ ! -f ".env" ]; then
        echo -e "${BLUE}Copie de .env.example vers .env${NC}"
        cp .env.example .env 2>/dev/null || echo "# Configuration Mobile" > .env
        echo -e "${GREEN}✓${NC} Fichier .env créé"
    else
        echo -e "${GREEN}✓${NC} Fichier .env existe"
    fi
    
    echo -e "${BLUE}Installation des dépendances Flutter...${NC}"
    cd patient
    flutter pub get
    echo -e "${GREEN}✓${NC} Dépendances installées"
else
    echo -e "${YELLOW}⚠ Flutter non installé, configuration Mobile ignorée${NC}"
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Résumé
echo -e "${GREEN}✅ Configuration terminée !${NC}"
echo ""
echo -e "${BLUE}📂 Arborescence du projet :${NC}"
echo ""
echo "$WORKSPACE_DIR/"
echo "├── clinique-n-api/          (Backend FastAPI)"
echo "├── clinique-n-frontend/     (Frontend React/Next.js)"
echo "└── clinique-n-mobile/       (Mobile Flutter)"
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}🚀 Commandes de démarrage :${NC}"
echo ""
echo -e "${BLUE}Backend (API) :${NC}"
echo "  cd $WORKSPACE_DIR/clinique-n-api"
echo "  docker compose up -d"
echo "  ./check_health.sh"
echo "  → API: http://localhost:8000"
echo "  → Docs: http://localhost:8000/docs"
echo ""
echo -e "${BLUE}Frontend (React) :${NC}"
echo "  cd $WORKSPACE_DIR/clinique-n-frontend"
echo "  pnpm dev"
echo "  → Admin: http://localhost:3000"
echo "  → Médecin: http://localhost:3001"
echo "  → Réceptionniste: http://localhost:3002"
echo "  → Public: http://localhost:3003"
echo ""
echo -e "${BLUE}Mobile (Flutter) :${NC}"
echo "  cd $WORKSPACE_DIR/clinique-n-mobile/patient"
echo "  flutter run"
echo "  → Lance l'app sur l'émulateur/device"
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}📚 Documentation :${NC}"
echo "  • Backend: $WORKSPACE_DIR/clinique-n-api/README.md"
echo "  • Frontend: $WORKSPACE_DIR/clinique-n-frontend/README.md"
echo "  • Mobile: $WORKSPACE_DIR/clinique-n-mobile/README.md"
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}🎉 Bon développement avec Clinique N !${NC}"
echo ""
