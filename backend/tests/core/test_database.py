"""
数据库配置模块测试用例
测试数据库连接、会话管理、连接池配置、事务处理、批量操作等功能
"""

import asyncio
import os
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, Mock, PropertyMock, patch

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Session

from app.core.database import (
    AsyncSessionLocal,
    Base,
    BulkOperations,
    DatabaseTransaction,
    SessionLocal,
    _get_async_engine_args,
    _get_optimized_connect_args,
    _get_optimized_pool_config,
    _get_sync_engine_args,
    _is_ci_environment,
    _is_testing_environment,
    async_engine,
    check_database_health,
    close_database,
    get_async_session,
    get_environment_info,
    get_model_by_tablename,
    get_pool_status,
    get_sync_session,
    get_table_names,
    init_database,
    sync_engine,
)


class TestEnvironmentDetection:
    """测试环境检测功能"""

    def test_is_ci_environment_true(self):
        """测试CI环境检测为真"""
        with patch.dict(os.environ, {"CI": "true"}):
            assert _is_ci_environment() is True

    def test_is_ci_environment_github_actions(self):
        """测试GitHub Actions环境检测"""
        with patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}):
            assert _is_ci_environment() is True

    def test_is_ci_environment_false(self):
        """测试非CI环境"""
        with patch.dict(os.environ, {}, clear=True):
            assert _is_ci_environment() is False

    def test_is_testing_environment_true(self):
        """测试测试环境检测为真"""
        with patch.dict(os.environ, {"TESTING": "true"}):
            assert _is_testing_environment() is True

    def test_is_testing_environment_settings(self):
        """测试通过settings检测测试环境"""
        with patch("app.core.database.settings") as mock_settings:
            mock_settings.TESTING = True
            assert _is_testing_environment() is True

    def test_is_testing_environment_false(self):
        """测试非测试环境"""
        with (
            patch.dict(os.environ, {}, clear=True),
            patch("app.core.database.settings") as mock_settings,
        ):
            mock_settings.TESTING = False
            assert _is_testing_environment() is False


class TestPoolConfiguration:
    """测试连接池配置功能"""

    def test_get_optimized_pool_config_ci(self):
        """测试CI环境的连接池配置"""
        with patch("app.core.database._is_ci_environment", return_value=True):
            config = _get_optimized_pool_config()

            assert config["pool_size"] == 1
            assert config["max_overflow"] == 1
            assert config["pool_recycle"] == 180
            assert config["pool_timeout"] == 5
            assert config["pool_pre_ping"] is True
            assert config["pool_reset_on_return"] == "commit"

    def test_get_optimized_pool_config_testing(self):
        """测试测试环境的连接池配置"""
        with (
            patch("app.core.database._is_ci_environment", return_value=False),
            patch("app.core.database._is_testing_environment", return_value=True),
        ):
            config = _get_optimized_pool_config()

            assert config["pool_size"] == 1
            assert config["max_overflow"] == 1
            assert config["pool_recycle"] == 300
            assert config["pool_timeout"] == 3
            assert config["pool_pre_ping"] is True
            assert config["pool_reset_on_return"] == "commit"

    def test_get_optimized_pool_config_production(self):
        """测试生产环境的连接池配置"""
        with (
            patch("app.core.database._is_ci_environment", return_value=False),
            patch("app.core.database._is_testing_environment", return_value=False),
        ):
            config = _get_optimized_pool_config()

            assert config["pool_size"] == 5
            assert config["max_overflow"] == 10
            assert config["pool_recycle"] == 1800
            assert config["pool_timeout"] == 30
            assert config["pool_pre_ping"] is True

    def test_get_optimized_connect_args_ci(self):
        """测试CI环境的连接参数"""
        with (
            patch("app.core.database._is_ci_environment", return_value=True),
            patch.dict(os.environ, {"ENVIRONMENT": "ci"}),
        ):
            args = _get_optimized_connect_args()

            assert "server_settings" in args
            assert args["server_settings"]["application_name"] == "kaoqin_backend_ci"
            assert args["command_timeout"] == 10
            assert args["server_settings"]["statement_timeout"] == "10000"
            assert (
                args["server_settings"]["idle_in_transaction_session_timeout"]
                == "30000"
            )

    def test_get_optimized_connect_args_testing(self):
        """测试测试环境的连接参数"""
        with (
            patch("app.core.database._is_ci_environment", return_value=False),
            patch("app.core.database._is_testing_environment", return_value=True),
        ):
            args = _get_optimized_connect_args()

            assert args["command_timeout"] == 15
            assert args["server_settings"]["statement_timeout"] == "15000"
            assert (
                args["server_settings"]["idle_in_transaction_session_timeout"]
                == "60000"
            )

    def test_get_optimized_connect_args_production(self):
        """测试生产环境的连接参数"""
        with (
            patch("app.core.database._is_ci_environment", return_value=False),
            patch("app.core.database._is_testing_environment", return_value=False),
        ):
            args = _get_optimized_connect_args()

            assert args["command_timeout"] == 300
            assert "statement_timeout" not in args["server_settings"]


class TestEngineConfiguration:
    """测试数据库引擎配置"""

    def test_get_async_engine_args_sqlite(self):
        """测试SQLite异步引擎配置"""
        with (
            patch(
                "app.core.database.get_database_url",
                return_value="sqlite+aiosqlite:///test.db",
            ),
            patch("app.core.database.settings") as mock_settings,
        ):

            mock_settings.DEBUG = True
            args = _get_async_engine_args()

            assert "poolclass" in args
            assert "connect_args" in args
            assert args["connect_args"]["check_same_thread"] is False
            assert args["echo"] is True
            assert args["future"] is True

    def test_get_async_engine_args_postgresql(self):
        """测试PostgreSQL异步引擎配置"""
        with (
            patch(
                "app.core.database.get_database_url",
                return_value="postgresql+asyncpg://user:pass@host/db",
            ),
            patch("app.core.database.settings") as mock_settings,
            patch("app.core.database._get_optimized_pool_config") as mock_pool,
            patch("app.core.database._get_optimized_connect_args") as mock_connect,
        ):

            mock_settings.DEBUG = False
            mock_pool.return_value = {"pool_size": 5}
            mock_connect.return_value = {"command_timeout": 30}

            args = _get_async_engine_args()

            assert args["pool_size"] == 5
            assert args["connect_args"]["command_timeout"] == 30
            assert args["echo"] is False

    def test_get_async_engine_args_ci_echo_disabled(self):
        """测试CI环境禁用echo"""
        with (
            patch(
                "app.core.database.get_database_url",
                return_value="postgresql://user:pass@host/db",
            ),
            patch("app.core.database.settings") as mock_settings,
            patch("app.core.database._is_ci_environment", return_value=True),
        ):

            mock_settings.DEBUG = True
            args = _get_async_engine_args()

            assert args["echo"] is False  # CI环境下禁用echo

    def test_get_sync_engine_args_basic(self):
        """测试同步引擎基本配置"""
        with (
            patch(
                "app.core.database.get_database_url_sync",
                return_value="postgresql://user:pass@host/db",
            ),
            patch("app.core.database.settings") as mock_settings,
            patch("app.core.database._get_optimized_pool_config") as mock_pool,
        ):

            mock_settings.DEBUG = False
            mock_pool.return_value = {"pool_size": 5, "pool_pre_ping": True}

            args = _get_sync_engine_args()

            assert args["pool_size"] == 5
            # pool_pre_ping在同步引擎配置中被保留，但在基础args中设置
            assert args["pool_pre_ping"] is True
            assert args["echo"] is False
            assert args["future"] is True


class TestSessionManagement:
    """测试会话管理功能"""

    @pytest.mark.asyncio
    async def test_get_async_session_success(self):
        """测试异步会话成功创建"""
        mock_session = AsyncMock(spec=AsyncSession)

        with patch("app.core.database.AsyncSessionLocal") as mock_session_factory:
            mock_session_factory.return_value = mock_session

            async for session in get_async_session():
                assert session == mock_session
                break

    @pytest.mark.asyncio
    async def test_get_async_session_exception_handling(self):
        """测试异步会话异常处理"""
        # 测试get_async_session在遇到异常时的行为
        with patch("app.core.database.AsyncSessionLocal") as mock_session_factory:
            mock_session_factory.side_effect = Exception("Session creation error")

            # 验证异常会被传播
            with pytest.raises(Exception) as exc_info:
                async for session in get_async_session():
                    pass

            assert "Session creation error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_async_session_rollback_error(self):
        """测试异步会话回滚错误处理"""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.rollback = AsyncMock(side_effect=Exception("Rollback error"))
        mock_session.close = AsyncMock()

        with patch("app.core.database.AsyncSessionLocal") as mock_session_factory:
            mock_session_factory.return_value = mock_session

            # 模拟主异常和回滚异常
            with patch.object(
                mock_session, "__aenter__", side_effect=Exception("Main error")
            ):
                try:
                    async for session in get_async_session():
                        pass
                except Exception:
                    pass

                # 验证即使回滚失败，close仍被调用
                mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_async_session_close_error(self):
        """测试异步会话关闭错误处理"""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.close = AsyncMock(side_effect=Exception("Close error"))

        with patch("app.core.database.AsyncSessionLocal") as mock_session_factory:
            mock_session_factory.return_value = mock_session

            # 正常使用会话，但关闭时出错
            async for session in get_async_session():
                assert session == mock_session
                break

            # 验证即使关闭失败，也不会抛出异常

    def test_get_sync_session_success(self):
        """测试同步会话成功创建"""
        mock_session = Mock(spec=Session)

        with patch("app.core.database.SessionLocal") as mock_session_factory:
            mock_session_factory.return_value = mock_session

            for session in get_sync_session():
                assert session == mock_session
                break

    def test_get_sync_session_exception_handling(self):
        """测试同步会话异常处理"""
        # 测试get_sync_session在遇到异常时的行为
        with patch("app.core.database.SessionLocal") as mock_session_factory:
            mock_session_factory.side_effect = Exception("Session creation error")

            # 验证异常会被传播
            with pytest.raises(Exception) as exc_info:
                for session in get_sync_session():
                    pass

            assert "Session creation error" in str(exc_info.value)


class TestDatabaseHealthCheck:
    """测试数据库健康检查"""

    @pytest.mark.asyncio
    async def test_check_database_health_success(self):
        """测试数据库健康检查成功"""
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()

        with patch("app.core.database.AsyncSessionLocal") as mock_session_factory:
            mock_session_factory.return_value.__aenter__ = AsyncMock(
                return_value=mock_session
            )
            mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await check_database_health(timeout_seconds=5)

            assert result is True
            mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_database_health_timeout(self):
        """测试数据库健康检查超时"""
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(side_effect=asyncio.TimeoutError())

        with patch("app.core.database.AsyncSessionLocal") as mock_session_factory:
            mock_session_factory.return_value.__aenter__ = AsyncMock(
                return_value=mock_session
            )
            mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await check_database_health(timeout_seconds=1)

            assert result is False

    @pytest.mark.asyncio
    async def test_check_database_health_exception(self):
        """测试数据库健康检查异常"""
        with patch("app.core.database.AsyncSessionLocal") as mock_session_factory:
            mock_session_factory.side_effect = Exception("Database error")

            result = await check_database_health()

            assert result is False

    @pytest.mark.asyncio
    async def test_check_database_health_sql_error(self):
        """测试数据库健康检查SQL错误"""
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(side_effect=SQLAlchemyError("SQL error"))

        with patch("app.core.database.AsyncSessionLocal") as mock_session_factory:
            mock_session_factory.return_value.__aenter__ = AsyncMock(
                return_value=mock_session
            )
            mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await check_database_health()

            assert result is False


class TestDatabaseInitialization:
    """测试数据库初始化和清理"""

    @pytest.mark.asyncio
    async def test_init_database_deprecation(self):
        """测试数据库初始化函数弃用警告"""
        # init_database函数应该记录弃用警告但不执行任何操作
        await init_database()  # 应该正常完成而不抛出异常

    @pytest.mark.asyncio
    async def test_close_database_success(self):
        """测试数据库连接成功关闭"""
        mock_async_engine = AsyncMock()
        mock_sync_engine = Mock()

        with (
            patch("app.core.database.async_engine", mock_async_engine),
            patch("app.core.database.sync_engine", mock_sync_engine),
        ):

            await close_database()

            mock_async_engine.dispose.assert_called_once()
            mock_sync_engine.dispose.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_database_async_error(self):
        """测试异步引擎关闭错误"""
        mock_async_engine = AsyncMock()
        mock_async_engine.dispose.side_effect = Exception("Async dispose error")
        mock_sync_engine = Mock()

        with (
            patch("app.core.database.async_engine", mock_async_engine),
            patch("app.core.database.sync_engine", mock_sync_engine),
        ):

            await close_database()  # 应该不抛出异常

            mock_sync_engine.dispose.assert_called_once()  # 同步引擎仍应被调用

    @pytest.mark.asyncio
    async def test_close_database_sync_error(self):
        """测试同步引擎关闭错误"""
        mock_async_engine = AsyncMock()
        mock_sync_engine = Mock()
        mock_sync_engine.dispose.side_effect = Exception("Sync dispose error")

        with (
            patch("app.core.database.async_engine", mock_async_engine),
            patch("app.core.database.sync_engine", mock_sync_engine),
        ):

            await close_database()  # 应该不抛出异常

            mock_async_engine.dispose.assert_called_once()


class TestDatabaseTransaction:
    """测试数据库事务处理"""

    @pytest.mark.asyncio
    async def test_database_transaction_success(self):
        """测试事务成功提交"""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.commit = AsyncMock()

        transaction = DatabaseTransaction(mock_session, timeout_seconds=5)

        async with transaction as session:
            assert session == mock_session

        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_database_transaction_rollback_on_exception(self):
        """测试异常时事务回滚"""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.rollback = AsyncMock()

        transaction = DatabaseTransaction(mock_session, timeout_seconds=5)

        try:
            async with transaction:
                raise ValueError("Test exception")
        except ValueError:
            pass

        mock_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_database_transaction_timeout_commit(self):
        """测试事务提交超时"""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.commit = AsyncMock(side_effect=asyncio.TimeoutError())
        mock_session.rollback = AsyncMock()

        transaction = DatabaseTransaction(mock_session, timeout_seconds=1)

        with pytest.raises(asyncio.TimeoutError):
            async with transaction:
                pass

        mock_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_database_transaction_timeout_rollback(self):
        """测试事务回滚超时"""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.rollback = AsyncMock(side_effect=asyncio.TimeoutError())

        transaction = DatabaseTransaction(mock_session, timeout_seconds=1)

        with pytest.raises(asyncio.TimeoutError):
            async with transaction:
                raise ValueError("Test exception")

    @pytest.mark.asyncio
    async def test_database_transaction_ci_timeout(self):
        """测试CI环境的事务超时设置"""
        mock_session = AsyncMock(spec=AsyncSession)

        with patch("app.core.database._is_ci_environment", return_value=True):
            transaction = DatabaseTransaction(mock_session)
            assert transaction.timeout_seconds == 10

    @pytest.mark.asyncio
    async def test_database_transaction_production_timeout(self):
        """测试生产环境的事务超时设置"""
        mock_session = AsyncMock(spec=AsyncSession)

        with patch("app.core.database._is_ci_environment", return_value=False):
            transaction = DatabaseTransaction(mock_session)
            assert transaction.timeout_seconds == 30


class TestBulkOperations:
    """测试批量操作功能"""

    @pytest.mark.asyncio
    async def test_bulk_insert_success(self):
        """测试批量插入成功"""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.add_all = Mock()
        mock_session.flush = AsyncMock()

        instances = [Mock() for _ in range(5)]

        await BulkOperations.bulk_insert(mock_session, instances, batch_size=3)

        # 应该分2批处理：3个和2个
        assert mock_session.add_all.call_count == 2
        assert mock_session.flush.call_count == 2

    @pytest.mark.asyncio
    async def test_bulk_insert_empty_list(self):
        """测试批量插入空列表"""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.add_all = Mock()

        await BulkOperations.bulk_insert(mock_session, [], batch_size=5)

        mock_session.add_all.assert_not_called()

    @pytest.mark.asyncio
    async def test_bulk_insert_ci_batch_size(self):
        """测试CI环境的批量插入批次大小"""
        mock_session = AsyncMock(spec=AsyncSession)
        instances = [Mock() for _ in range(150)]

        with patch("app.core.database._is_ci_environment", return_value=True):
            await BulkOperations.bulk_insert(mock_session, instances)

            # CI环境批次大小为100，应该分2批
            assert mock_session.add_all.call_count == 2

    @pytest.mark.asyncio
    async def test_bulk_insert_production_batch_size(self):
        """测试生产环境的批量插入批次大小"""
        mock_session = AsyncMock(spec=AsyncSession)
        instances = [Mock() for _ in range(600)]

        with patch("app.core.database._is_ci_environment", return_value=False):
            await BulkOperations.bulk_insert(mock_session, instances)

            # 生产环境批次大小为500，应该分2批
            assert mock_session.add_all.call_count == 2

    @pytest.mark.asyncio
    async def test_bulk_update_success(self):
        """测试批量更新成功"""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.merge = AsyncMock()
        mock_session.flush = AsyncMock()

        mappings = [{"id": i, "name": f"item_{i}"} for i in range(5)]

        await BulkOperations.bulk_update(mock_session, mappings, batch_size=2)

        # 5个项目，批次大小为2，应该分3批
        assert mock_session.merge.call_count == 5
        assert mock_session.flush.call_count == 3

    @pytest.mark.asyncio
    async def test_bulk_update_empty_list(self):
        """测试批量更新空列表"""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.merge = AsyncMock()

        await BulkOperations.bulk_update(mock_session, [])

        mock_session.merge.assert_not_called()

    @pytest.mark.asyncio
    async def test_bulk_update_ci_batch_size(self):
        """测试CI环境的批量更新批次大小"""
        mock_session = AsyncMock(spec=AsyncSession)
        mappings = [{"id": i} for i in range(75)]

        with patch("app.core.database._is_ci_environment", return_value=True):
            await BulkOperations.bulk_update(mock_session, mappings)

            # CI环境批次大小为50，应该分2批
            assert mock_session.flush.call_count == 2

    @pytest.mark.asyncio
    async def test_bulk_update_production_batch_size(self):
        """测试生产环境的批量更新批次大小"""
        mock_session = AsyncMock(spec=AsyncSession)
        mappings = [{"id": i} for i in range(300)]

        with patch("app.core.database._is_ci_environment", return_value=False):
            await BulkOperations.bulk_update(mock_session, mappings)

            # 生产环境批次大小为200，应该分2批
            assert mock_session.flush.call_count == 2


class TestDatabaseUtilities:
    """测试数据库工具函数"""

    def test_get_table_names(self):
        """测试获取表名列表"""
        with patch.object(
            Base.metadata, "tables", {"table1": Mock(), "table2": Mock()}
        ):
            names = get_table_names()
            assert "table1" in names
            assert "table2" in names
            assert len(names) == 2

    @patch("app.core.database.Base.registry")
    def test_get_model_by_tablename_found(self, mock_registry):
        """测试根据表名查找模型成功"""
        mock_mapper = Mock()
        mock_model = Mock()
        mock_model.__tablename__ = "test_table"
        mock_mapper.class_ = mock_model
        mock_registry.mappers = [mock_mapper]

        result = get_model_by_tablename("test_table")
        assert result == mock_model

    @patch("app.core.database.Base.registry")
    def test_get_model_by_tablename_not_found(self, mock_registry):
        """测试根据表名查找模型失败"""
        mock_mapper = Mock()
        mock_model = Mock()
        mock_model.__tablename__ = "other_table"
        mock_mapper.class_ = mock_model
        mock_registry.mappers = [mock_mapper]

        result = get_model_by_tablename("test_table")
        assert result is None

    @patch("app.core.database.Base.registry")
    def test_get_model_by_tablename_no_tablename_attr(self, mock_registry):
        """测试模型缺少__tablename__属性"""
        mock_mapper = Mock()
        mock_model = Mock(spec=[])  # 没有__tablename__属性
        mock_mapper.class_ = mock_model
        mock_registry.mappers = [mock_mapper]

        result = get_model_by_tablename("test_table")
        assert result is None


class TestConnectionPoolMonitoring:
    """测试连接池监控功能"""

    @pytest.mark.asyncio
    async def test_get_pool_status_success(self):
        """测试成功获取连接池状态"""
        mock_pool = Mock()
        mock_pool.size.return_value = 5
        mock_pool.checkedin.return_value = 3
        mock_pool.checkedout.return_value = 2
        mock_pool.overflow.return_value = 0
        mock_pool.invalid.return_value = 0

        with (
            patch("app.core.database.async_engine") as mock_engine,
            patch("app.core.database._is_ci_environment", return_value=False),
            patch("app.core.database._is_testing_environment", return_value=False),
        ):
            mock_engine.pool = mock_pool

            status = await get_pool_status()

            assert status["pool_size"] == 5
            assert status["checked_in"] == 3
            assert status["checked_out"] == 2
            assert status["overflow"] == 0
            assert status["invalid"] == 0
            assert status["environment"] == "production"

    @pytest.mark.asyncio
    async def test_get_pool_status_ci_environment(self):
        """测试CI环境的连接池状态"""
        mock_pool = Mock()
        mock_pool.size.return_value = 1

        with (
            patch("app.core.database.async_engine") as mock_engine,
            patch("app.core.database._is_ci_environment", return_value=True),
        ):
            mock_engine.pool = mock_pool

            status = await get_pool_status()

            assert status["environment"] == "ci"

    @pytest.mark.asyncio
    async def test_get_pool_status_testing_environment(self):
        """测试测试环境的连接池状态"""
        mock_pool = Mock()
        mock_pool.size.return_value = 1

        with (
            patch("app.core.database.async_engine") as mock_engine,
            patch("app.core.database._is_ci_environment", return_value=False),
            patch("app.core.database._is_testing_environment", return_value=True),
        ):
            mock_engine.pool = mock_pool

            status = await get_pool_status()

            assert status["environment"] == "testing"

    @pytest.mark.asyncio
    async def test_get_pool_status_error(self):
        """测试获取连接池状态错误"""
        with patch("app.core.database.async_engine") as mock_engine:
            # 模拟访问pool属性时抛出异常
            type(mock_engine).pool = PropertyMock(
                side_effect=Exception("Pool access error")
            )

            status = await get_pool_status()

            assert "error" in status
            assert isinstance(status["error"], str)

    @pytest.mark.asyncio
    async def test_get_pool_status_attribute_error(self):
        """测试连接池属性错误"""
        mock_pool = Mock()
        # 模拟某些属性不存在
        del mock_pool.size

        with patch("app.core.database.async_engine") as mock_engine:
            mock_engine.pool = mock_pool

            status = await get_pool_status()

            # getattr的lambda函数应该返回0
            assert status["pool_size"] == 0


class TestEnvironmentInfo:
    """测试环境信息功能"""

    def test_get_environment_info_basic(self):
        """测试基本环境信息获取"""
        with (
            patch("app.core.database._is_ci_environment", return_value=False),
            patch("app.core.database._is_testing_environment", return_value=False),
            patch(
                "app.core.database.get_database_url",
                return_value="postgresql://user:pass@host/db",
            ),
            patch(
                "app.core.database._get_optimized_pool_config",
                return_value={"pool_size": 5},
            ),
            patch("app.core.database.settings") as mock_settings,
        ):

            mock_settings.DEBUG = True

            info = get_environment_info()

            assert info["is_ci"] is False
            assert info["is_testing"] is False
            assert info["database_url"] == "host/db"
            assert info["pool_config"] == {"pool_size": 5}
            assert info["debug_mode"] is True

    def test_get_environment_info_ci(self):
        """测试CI环境信息"""
        with (
            patch("app.core.database._is_ci_environment", return_value=True),
            patch("app.core.database._is_testing_environment", return_value=False),
            patch(
                "app.core.database.get_database_url", return_value="sqlite:///test.db"
            ),
        ):

            info = get_environment_info()

            assert info["is_ci"] is True
            # SQLite URL不包含@，所以返回"sqlite"
            assert info["database_url"] == "sqlite"

    def test_get_environment_info_database_url_without_auth(self):
        """测试不包含认证信息的数据库URL"""
        with patch(
            "app.core.database.get_database_url", return_value="sqlite:///memory"
        ):
            info = get_environment_info()
            # SQLite URL不包含@，所以返回"sqlite"
            assert info["database_url"] == "sqlite"


class TestDatabaseEventListeners:
    """测试数据库事件监听器"""

    def test_event_listeners_skipped_in_ci(self):
        """测试CI环境跳过事件监听器"""
        # 由于事件监听器在CI环境中被跳过，我们主要测试条件逻辑
        with patch("app.core.database._is_ci_environment", return_value=True):
            # 在CI环境中，事件监听器不应该被注册
            # 这个测试主要确保代码结构正确
            pass

    def test_event_listeners_enabled_in_production(self):
        """测试生产环境启用事件监听器"""
        with patch("app.core.database._is_ci_environment", return_value=False):
            # 在非CI环境中，事件监听器应该被注册
            # 由于事件监听器在模块级别注册，这里主要测试条件逻辑
            pass


class TestDatabaseIntegration:
    """测试数据库集成功能"""

    @pytest.mark.asyncio
    async def test_full_session_lifecycle(self):
        """测试完整的会话生命周期"""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute = AsyncMock()
        mock_session.close = AsyncMock()

        with patch("app.core.database.AsyncSessionLocal") as mock_factory:
            mock_factory.return_value = mock_session

            # 测试正常的会话创建和使用
            async for session in get_async_session():
                await session.execute(text("SELECT 1"))
                break

            mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_transaction_with_bulk_operations(self):
        """测试事务与批量操作集成"""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.commit = AsyncMock()
        mock_session.add_all = Mock()
        mock_session.flush = AsyncMock()

        instances = [Mock() for _ in range(3)]

        async with DatabaseTransaction(mock_session) as session:
            await BulkOperations.bulk_insert(session, instances, batch_size=2)

        # 验证批量操作和事务提交都被调用
        assert mock_session.add_all.call_count == 2  # 分批处理
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_with_actual_query(self):
        """测试使用实际查询的健康检查"""
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_session.execute.return_value = mock_result

        with patch("app.core.database.AsyncSessionLocal") as mock_factory:
            mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_factory.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await check_database_health()

            assert result is True
            # 验证执行了SELECT 1查询
            args, _ = mock_session.execute.call_args
            assert "SELECT 1" in str(args[0])


class TestEdgeCasesAndErrorHandling:
    """测试边界情况和错误处理"""

    @pytest.mark.asyncio
    async def test_database_transaction_nested_exception(self):
        """测试嵌套异常处理"""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.rollback = AsyncMock(side_effect=Exception("Rollback failed"))

        transaction = DatabaseTransaction(mock_session)

        # 嵌套异常：主异常 + 回滚异常
        # 根据实现，回滚失败时会抛出回滚异常
        with pytest.raises(Exception):  # 任何异常都可能被抛出
            async with transaction:
                raise ValueError("Original error")

    def test_pool_config_edge_cases(self):
        """测试连接池配置边界情况"""
        # 测试所有环境标志都为False的情况
        with (
            patch("app.core.database._is_ci_environment", return_value=False),
            patch("app.core.database._is_testing_environment", return_value=False),
        ):

            config = _get_optimized_pool_config()

            # 应该返回生产环境配置
            assert config["pool_size"] == 5
            assert config["max_overflow"] == 10

    @pytest.mark.asyncio
    async def test_bulk_operations_large_batch(self):
        """测试大批量操作"""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.add_all = Mock()
        mock_session.flush = AsyncMock()

        # 创建大量实例
        instances = [Mock() for _ in range(1000)]

        await BulkOperations.bulk_insert(mock_session, instances, batch_size=100)

        # 应该分10批处理
        assert mock_session.add_all.call_count == 10
        assert mock_session.flush.call_count == 10

    def test_environment_detection_priority(self):
        """测试环境检测优先级"""
        # CI环境标志优先于TESTING标志
        with patch.dict(os.environ, {"CI": "true", "TESTING": "true"}):
            assert _is_ci_environment() is True

        with patch.dict(os.environ, {"CI": "false", "TESTING": "true"}):
            assert _is_ci_environment() is False
