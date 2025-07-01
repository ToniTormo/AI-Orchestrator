"""
Agent Health Service

Handles health checks and status monitoring for agents
"""

from datetime import datetime
from typing import Dict, Any
from src.config import settings
from src.utils.logging import setup_logger
from src.utils.exceptions_control import create_error, AgentError
from src.domain.models.agent_model import AgentStatus
from src.infrastructure.services import AsyncServiceBase

class AgentHealthService:
    """Service for managing agent health checks and status"""

    def __init__(self):
        """Initialize the health service"""
        self.logger = setup_logger(
            "agents.health",
            settings.logging.module_levels.get("agents", settings.logging.level)
        )
        self.agent_status: Dict[str, AgentStatus] = {}

    async def check_agent_health(self, agent_id: str, agent: AsyncServiceBase) -> AgentStatus:
        """
        Check the health of an agent by verifying its initialization status.
        
        Args:
            agent_id: ID of the agent to check
            agent: Agent instance to check
            
        Returns:
            Updated agent status
        """
        try:
            self.logger.debug(f"[AgentHealth] Checking health for agent: {agent_id}")
            
            # Get current status or create new
            status = self.agent_status.get(agent_id, AgentStatus(
                registered_at=datetime.now(),
                status="unknown",
                last_health_check=datetime.now()
            ))
            
            # An agent is considered healthy if it is initialized.
            is_healthy = agent.is_initialized
            status.last_health_check = datetime.now()
            status.healthy = is_healthy
            
            # Update status based on health check
            if is_healthy:
                status.status = "available"
                status.error = None
            else:
                status.status = "error"
                status.error = "Agent not initialized"
            
            # Store updated status
            self.agent_status[agent_id] = status
            
            self.logger.debug(f"[AgentHealth] Health check completed for agent {agent_id}: {is_healthy}")
            return status
            
        except Exception as e:
            if agent_id in self.agent_status:
                self.agent_status[agent_id].status = "error"
                self.agent_status[agent_id].error = str(e)
            raise create_error(AgentError, f"Error checking agent health: {e}", "AgentHealth")

    def get_agent_status(self, agent_id: str) -> AgentStatus:
        """
        Get current status of an agent with explicit error on not found
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            Current agent status
        """
        status = self.agent_status.get(agent_id)
        if status is None:
            raise create_error(AgentError, f"No status found for agent '{agent_id}'. Available agents: {list(self.agent_status.keys())}", "AgentHealth")
        return status

    def update_agent_status(self, agent_id: str, status: AgentStatus) -> None:
        """
        Update agent status
        
        Args:
            agent_id: ID of the agent
            status: New status to set
        """
        self.agent_status[agent_id] = status 