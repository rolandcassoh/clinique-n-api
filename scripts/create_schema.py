#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path

# Add project root to python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import Base, engine

# Import all modules to ensure they are registered in metadata
MODULES = [
    "app.modules.client.infrastructure.modeles",
    "app.modules.auth.infrastructure.modeles",
    "app.modules.clinic.infrastructure.modeles",
    "app.modules.consultation.infrastructure.modeles",
    "app.modules.taxe.infrastructure.modeles",
    "app.modules.portefeuille.infrastructure.modeles",
    "app.modules.produit.infrastructure.modeles",
    "app.modules.abonnement.infrastructure.modeles",
    "app.modules.facturation.infrastructure.modeles",
    "app.modules.blog.infrastructure.modeles",
    "app.modules.rendez_vous.infrastructure.modeles",
    "app.modules.promotion.infrastructure.modeles",
    "app.modules.service.infrastructure.modeles",
    "app.modules.monde.infrastructure.modeles",
    "app.modules.page.infrastructure.modeles",
    "app.modules.constante.infrastructure.modeles",
    "app.modules.etiquette.infrastructure.modeles",
    "app.modules.langue.infrastructure.modeles",
    "app.modules.devise.infrastructure.modeles",
    "app.modules.logistique.infrastructure.modeles",
    "app.modules.faq.infrastructure.modeles",
    "app.modules.commission.infrastructure.modeles",
    "app.modules.demande_service.infrastructure.modeles",
    "app.modules.slider.infrastructure.modeles",
    "app.modules.signe_vital.infrastructure.modeles",
]

for module in MODULES:
    __import__(module)

async def main():
    print("Creating tables in French in clinique_dev...")
    async with engine.begin() as conn:
        # Recreate schema
        await conn.run_sync(Base.metadata.create_all)
    print("All tables created successfully.")

if __name__ == "__main__":
    asyncio.run(main())
