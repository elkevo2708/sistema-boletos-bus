from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args={"connect_timeout": 10},
)
# aiomysql exige ping(reconnect). El dialecto de SQLAlchemy 2.0.36 lo llama
# sin argumentos y tumba el pool en el segundo checkout.
engine.sync_engine.dialect._send_false_to_ping = True
SesionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
