"""Dashboard routes."""

from fastapi import APIRouter, Depends

from src.app.composition import get_dashboard_stats_use_case
from src.app.features.dashboard.application.dtos.dashboard_dto import DashboardStatsResponse
from src.app.features.dashboard.application.use_cases.get_dashboard_stats import GetDashboardStatsUseCase
from src.app.shared.application.request_context import RequestContext
from src.app.shared.presentation.auth_dependencies import get_request_context


router = APIRouter()


@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    ctx: RequestContext = Depends(get_request_context),
    use_case: GetDashboardStatsUseCase = Depends(get_dashboard_stats_use_case),
) -> DashboardStatsResponse:
    """
    Get dashboard statistics for the caller's workspace.

    Requires authentication. Returns aggregated counts of the workspace's projects and
    stories, plus the stories assigned to the caller.

    Args:
        ctx: Caller identity and workspace (from JWT)
        use_case: Injected GetDashboardStatsUseCase

    Returns:
        DashboardStatsResponse with statistics

    Raises:
        401: Unauthorized
        500: Internal server error
    """
    return await use_case.execute(ctx)
