"""
Test helpers for unit tests.
Provides utilities for creating proper mocks that avoid SQLAlchemy session issues.
"""

from unittest.mock import Mock, AsyncMock
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import RepairTask, MonitoringTask, AssistanceTask, TaskStatus, TaskType, TaskCategory, TaskPriority
from app.models.member import Member, UserRole


class MockSessionBuilder:
    """Builder for creating properly configured mock AsyncSession objects."""
    
    def __init__(self):
        self.session = AsyncMock(spec=AsyncSession)
        self._setup_basic_methods()
    
    def _setup_basic_methods(self):
        """Setup basic AsyncSession methods."""
        # Core async methods
        self.session.commit = AsyncMock()
        self.session.rollback = AsyncMock()
        self.session.refresh = AsyncMock()
        self.session.flush = AsyncMock()
        self.session.close = AsyncMock()
        self.session.execute = AsyncMock()
        
        # Synchronous methods
        self.session.add = Mock()
        self.session.delete = Mock()
        self.session.merge = Mock()
        
        # Transaction state
        self.session.in_transaction = Mock(return_value=True)
        
        # Session state properties
        self.session.identity_map = {}
        self.session._new = set()
        self.session._dirty = set()
        
    def with_query_result(self, mock_result):
        """Configure session.execute to return a specific result."""
        self.session.execute.return_value = mock_result
        return self
    
    def with_query_results(self, mock_results):
        """Configure session.execute to return multiple results in sequence."""
        self.session.execute.side_effect = mock_results
        return self
        
    def build(self) -> AsyncMock:
        """Build the configured mock session."""
        return self.session


class MockTaskBuilder:
    """Builder for creating properly configured task mocks."""
    
    @staticmethod
    def repair_task(
        id: int = 1,
        task_id: str = "T001",
        title: str = "Test Repair Task",
        status: TaskStatus = TaskStatus.PENDING,
        member_id: Optional[int] = None,
        **kwargs
    ) -> Mock:
        """Create a mock RepairTask that avoids session persistence issues."""
        mock_task = Mock(spec=RepairTask)
        
        # Set basic attributes
        mock_task.id = id
        mock_task.task_id = task_id
        mock_task.title = title
        mock_task.status = status
        mock_task.member_id = member_id
        
        # Set additional attributes from kwargs
        for key, value in kwargs.items():
            setattr(mock_task, key, value)
            
        # Set defaults for common attributes if not provided
        if not hasattr(mock_task, 'category'):
            mock_task.category = TaskCategory.NETWORK_REPAIR
        if not hasattr(mock_task, 'priority'):
            mock_task.priority = TaskPriority.MEDIUM
        if not hasattr(mock_task, 'task_type'):
            mock_task.task_type = TaskType.ONLINE
        if not hasattr(mock_task, 'base_work_minutes'):
            mock_task.base_work_minutes = 40
        if not hasattr(mock_task, 'work_minutes'):
            mock_task.work_minutes = 40
        if not hasattr(mock_task, 'rating'):
            mock_task.rating = None
        if not hasattr(mock_task, 'feedback'):
            mock_task.feedback = None
        if not hasattr(mock_task, 'description'):
            mock_task.description = "Default task description"
        if not hasattr(mock_task, 'tags'):
            mock_task.tags = []
            
        return mock_task
    
    @staticmethod
    def monitoring_task(
        id: int = 1,
        member_id: int = 1,
        title: str = "Test Monitoring Task",
        **kwargs
    ) -> Mock:
        """Create a mock MonitoringTask."""
        mock_task = Mock(spec=MonitoringTask)
        
        mock_task.id = id
        mock_task.member_id = member_id
        mock_task.title = title
        
        # Set additional attributes from kwargs
        for key, value in kwargs.items():
            setattr(mock_task, key, value)
            
        # Set defaults
        if not hasattr(mock_task, 'status'):
            mock_task.status = TaskStatus.COMPLETED
        if not hasattr(mock_task, 'work_minutes'):
            mock_task.work_minutes = 120
            
        return mock_task
    
    @staticmethod
    def assistance_task(
        id: int = 1,
        member_id: int = 1,
        title: str = "Test Assistance Task",
        **kwargs
    ) -> Mock:
        """Create a mock AssistanceTask."""
        mock_task = Mock(spec=AssistanceTask)
        
        mock_task.id = id
        mock_task.member_id = member_id
        mock_task.title = title
        
        # Set additional attributes from kwargs
        for key, value in kwargs.items():
            setattr(mock_task, key, value)
            
        # Set defaults
        if not hasattr(mock_task, 'status'):
            mock_task.status = TaskStatus.COMPLETED
        if not hasattr(mock_task, 'work_minutes'):
            mock_task.work_minutes = 180
            
        return mock_task


class MockMemberBuilder:
    """Builder for creating properly configured member mocks."""
    
    @staticmethod
    def member(
        id: int = 1,
        username: str = "testuser",
        name: str = "Test User",
        role: UserRole = UserRole.MEMBER,
        is_active: bool = True,
        **kwargs
    ) -> Mock:
        """Create a mock Member."""
        mock_member = Mock(spec=Member)
        
        mock_member.id = id
        mock_member.username = username
        mock_member.name = name
        mock_member.role = role
        mock_member.is_active = is_active
        
        # Set additional attributes from kwargs
        for key, value in kwargs.items():
            setattr(mock_member, key, value)
            
        # Set defaults
        if not hasattr(mock_member, 'student_id'):
            mock_member.student_id = f"202500{id:04d}"
        if not hasattr(mock_member, 'class_name'):
            mock_member.class_name = "测试班级"
        if not hasattr(mock_member, 'email'):
            mock_member.email = f"{username}@example.com"
            
        return mock_member
    
    @staticmethod
    def admin(id: int = 1, **kwargs) -> Mock:
        """Create a mock admin member."""
        return MockMemberBuilder.member(
            id=id,
            username=f"admin_{id}",
            name="管理员",
            role=UserRole.ADMIN,
            **kwargs
        )
    
    @staticmethod
    def group_leader(id: int = 2, **kwargs) -> Mock:
        """Create a mock group leader member."""
        return MockMemberBuilder.member(
            id=id,
            username=f"leader_{id}",
            name="组长",
            role=UserRole.GROUP_LEADER,
            **kwargs
        )
    
    @staticmethod
    def inactive_member(id: int = 3, **kwargs) -> Mock:
        """Create a mock inactive member."""
        return MockMemberBuilder.member(
            id=id,
            username=f"inactive_{id}",
            name="已停用成员",
            role=UserRole.MEMBER,
            is_active=False,
            **kwargs
        )


class MockResultBuilder:
    """Builder for creating mock database query results."""
    
    @staticmethod
    def single_result(obj: Any) -> Mock:
        """Create a mock result that returns a single object."""
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = obj
        mock_result.scalar.return_value = obj
        return mock_result
    
    @staticmethod
    def list_result(objects: list) -> Mock:
        """Create a mock result that returns a list of objects."""
        mock_result = Mock()
        mock_scalars = Mock()
        mock_scalars.all.return_value = objects
        mock_scalars.first.return_value = objects[0] if objects else None
        mock_result.scalars.return_value = mock_scalars
        return mock_result
    
    @staticmethod
    def empty_result() -> Mock:
        """Create a mock result that returns None/empty."""
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_result.scalar.return_value = None
        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        mock_scalars.first.return_value = None
        mock_result.scalars.return_value = mock_scalars
        return mock_result


# Convenience functions for common test scenarios
def create_mock_session() -> AsyncMock:
    """Create a basic mock session."""
    return MockSessionBuilder().build()


def create_mock_session_with_result(result_obj: Any) -> AsyncMock:
    """Create a mock session that returns a specific result."""
    mock_result = MockResultBuilder.single_result(result_obj)
    return MockSessionBuilder().with_query_result(mock_result).build()


def create_mock_session_with_results(result_objects: list) -> AsyncMock:
    """Create a mock session that returns multiple results in sequence."""
    mock_results = [MockResultBuilder.single_result(obj) for obj in result_objects]
    return MockSessionBuilder().with_query_results(mock_results).build()


def simulate_task_update(mock_task: Mock, **updates):
    """Simulate updating task attributes (for testing update operations)."""
    for key, value in updates.items():
        setattr(mock_task, key, value)
    return mock_task