import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.config import settings
from app.database import Base

# Import all models so Alembic detects them
from app.modules.abonnement.infrastructure.modeles import (  # noqa: F401
    PlanLimitationModel,
    SubscriptionModel,
    SubscriptionPlanModel,
)
from app.modules.auth.infrastructure.modeles import (  # noqa: F401
    ModelHasRoleModel,
    PersonalAccessTokenModel,
    RoleModel,
    UserModel,
    UserProfileModel,
)
from app.modules.blog.infrastructure.modeles import (  # noqa: F401
    BlogCategoryModel,
    BlogPostModel,
)
from app.modules.client.infrastructure.modeles import (  # noqa: F401
    OtherPatientModel,
)
from app.modules.clinic.infrastructure.modeles import (  # noqa: F401
    ClinicCategoryModel,
    ClinicModel,
    ClinicServiceModel,
    DoctorLeaveModel,
    DoctorModel,
    DoctorRatingModel,
    DoctorSessionModel,
    ReceptionistModel,
)
from app.modules.commission.infrastructure.modeles import (  # noqa: F401
    CommissionEarningModel,
    EmployeeCommissionModel,
    EmployeeEarningModel,
)
from app.modules.constante.infrastructure.modeles import (  # noqa: F401
    SettingModel,
)
from app.modules.consultation.infrastructure.modeles import (  # noqa: F401
    AppointmentBodyChartModel,
    EncounterMedicalReportModel,
    EncounterPrescriptionModel,
    PatientEncounterModel,
)
from app.modules.demande_service.infrastructure.modeles import (  # noqa: F401
    RequestServiceModel,
)
from app.modules.devise.infrastructure.modeles import (  # noqa: F401
    CurrencyModel,
)
from app.modules.etiquette.infrastructure.modeles import (  # noqa: F401
    TagModel,
)
from app.modules.facturation.infrastructure.modeles import (  # noqa: F401
    BillingItemModel,
    BillingRecordModel,
)
from app.modules.faq.infrastructure.modeles import (  # noqa: F401
    FAQModel,
)
from app.modules.langue.infrastructure.modeles import (  # noqa: F401
    LanguageModel,
)
from app.modules.logistique.infrastructure.modeles import (  # noqa: F401
    ShippingRateModel,
    ShippingZoneModel,
)
from app.modules.monde.infrastructure.modeles import (  # noqa: F401
    CityModel,
    CountryModel,
    StateModel,
)
from app.modules.page.infrastructure.modeles import (  # noqa: F401
    PageModel,
)
from app.modules.portefeuille.infrastructure.modeles import (  # noqa: F401
    PatientWalletModel,
    WalletHistoryModel,
)
from app.modules.produit.infrastructure.modeles import (  # noqa: F401
    BrandModel,
    CartItemModel,
    CartModel,
    OrderItemModel,
    OrderModel,
    ProductCategoryModel,
    ProductImageModel,
    ProductModel,
    ProductReviewModel,
    UnitModel,
    WishListItemModel,
    WishListModel,
)
from app.modules.promotion.infrastructure.modeles import (  # noqa: F401
    PromotionModel,
    PromotionUseModel,
)
from app.modules.rendez_vous.infrastructure.modeles import (  # noqa: F401
    AppointmentModel,
    AppointmentTransactionModel,
)
from app.modules.service.infrastructure.modeles import (  # noqa: F401
    ServiceCategoryModel,
    ServiceEmployeeModel,
    ServiceGalleryModel,
    ServiceModel,
    ServicePackageModel,
    ServiceReviewModel,
)
from app.modules.signe_vital.infrastructure.modeles import (  # noqa: F401
    VitalSignsModel,
)
from app.modules.slider.infrastructure.modeles import (  # noqa: F401
    SliderModel,
)
from app.modules.taxe.infrastructure.modeles import (  # noqa: F401
    TaxModel,
)

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
