"""Dashboard routes."""
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status

from src.app.features.dashboard.application.dtos.dashboard_dto import DashboardStatsResponse
from src.app.features.dashboard.application.use_cases.get_dashboard_stats import GetDashboardStatsUseCase
from src.app.features.dashboard.presentation.dependencies import get_get_dashboard_stats_use_case
from src.app.features.user.presentation.auth_dependencies import get_current_user

router = APIRouter()


@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    current_user: Dict[str, Any] = Depends(get_current_user),
    use_case: GetDashboardStatsUseCase = Depends(get_get_dashboard_stats_use_case),
) -> DashboardStatsResponse:
    """
    Get dashboard statistics for the current user.
    
    Requires authentication. Returns aggregated counts of projects and stories.
    
    Args:
        current_user: Current authenticated user
        use_case: Injected GetDashboardStatsUseCase
        
    Returns:
        DashboardStatsResponse with statistics
        
    Raises:
        401: Unauthorized
        500: Internal server error
    """
    user_id = current_user.get("sub")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    result = await use_case.execute(user_id)
    
    return result