"""Backlog view and Markdown export routes."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Response, status
from fastapi.params import Depends

from src.app.composition import get_export_backlog_markdown_use_case, get_get_project_backlog_use_case
from src.app.features.backlog.application.dtos.backlog_dto import BacklogStoryResponse, MarkdownExportRequest
from src.app.features.backlog.application.use_cases.export_backlog_markdown import ExportBacklogMarkdownUseCase
from src.app.features.backlog.application.use_cases.get_project_backlog import GetProjectBacklogUseCase
from src.app.features.projects.domain.exceptions.project_exceptions import ProjectNotFoundError
from src.app.shared.application.dtos.pagination_dto import PaginatedResponse
from src.app.shared.application.request_context import RequestContext
from src.app.shared.presentation.auth_dependencies import get_request_context, require_editor


router = APIRouter()

EMPTY_EXPORT_WARNING = "No approved stories match this scope."


@router.get("/{project_id}/backlog", response_model=PaginatedResponse[BacklogStoryResponse])
async def get_project_backlog(
    project_id: UUID,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    ctx: RequestContext = Depends(get_request_context),
    use_case: GetProjectBacklogUseCase = Depends(get_get_project_backlog_use_case),
) -> PaginatedResponse[BacklogStoryResponse]:
    """
    Get a project's approved backlog with acceptance criteria.

    Admin and Viewer. Drafts are excluded structurally — unapproved work lives in
    story_drafts and never reaches this table.

    Args:
        project_id: The project to read
        limit: Maximum number of stories per page
        offset: Number of stories to skip
        ctx: Caller identity and workspace (from JWT)
        use_case: Injected GetProjectBacklogUseCase

    Returns:
        PaginatedResponse of backlog stories in priority-then-age order

    Raises:
        401: Missing or invalid JWT
        404: Project not found
    """
    try:
        return await use_case.execute(project_id=project_id, ctx=ctx, limit=limit, offset=offset)
    except ProjectNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.post(
    "/{project_id}/exports/markdown",
    response_class=Response,
    # Declared explicitly: without it OpenAPI advertises a JSON body, and generated clients
    # mis-handle what is really a Markdown attachment carrying three custom headers.
    responses={
        200: {
            "content": {"text/markdown": {"schema": {"type": "string"}}},
            "description": "The backlog as a Markdown file.",
            "headers": {
                "Content-Disposition": {
                    "description": 'attachment; filename="<project>-backlog-<date>.md"',
                    "schema": {"type": "string"},
                },
                "X-Export-Story-Count": {
                    "description": "Number of stories in the document.",
                    "schema": {"type": "integer"},
                },
                "X-Export-Warning": {
                    "description": "Present when the scope matched nothing, or was truncated by the export cap.",
                    "schema": {"type": "string"},
                },
            },
        }
    },
)
async def export_backlog_markdown(
    project_id: UUID,
    scope: MarkdownExportRequest | None = None,
    ctx: RequestContext = Depends(require_editor),
    use_case: ExportBacklogMarkdownUseCase = Depends(get_export_backlog_markdown_use_case),
) -> Response:
    """
    Export a project's backlog as a downloadable Markdown file.

    Admin only — a Viewer may read the backlog but not take it away. An empty scope is
    warned about via X-Export-Warning rather than rejected, so the Admin still receives a
    usable template.

    Args:
        project_id: The project to export
        scope: Optional status and date-range narrowing; an absent body exports everything
        ctx: Caller identity and workspace (from JWT)
        use_case: Injected ExportBacklogMarkdownUseCase

    Returns:
        The Markdown document as a file attachment

    Raises:
        401: Missing or invalid JWT
        403: Caller is not an Admin
        404: Project not found
        422: Invalid scope (unknown status, inverted date range)
    """
    try:
        export = await use_case.execute(project_id=project_id, scope=scope or MarkdownExportRequest(), ctx=ctx)
    except ProjectNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error

    headers = {
        "Content-Disposition": f'attachment; filename="{export.filename}"',
        "X-Export-Story-Count": str(export.story_count),
        # Browsers hide non-standard headers from cross-origin JS unless they are exposed.
        "Access-Control-Expose-Headers": "Content-Disposition, X-Export-Story-Count, X-Export-Warning",
    }
    if export.story_count == 0:
        headers["X-Export-Warning"] = EMPTY_EXPORT_WARNING
    elif export.is_truncated:
        headers["X-Export-Warning"] = (
            f"This export contains the first {export.story_count} of {export.matched_count} matching "
            f"stories. Narrow the scope by status or date to export the rest."
        )

    return Response(content=export.content, media_type="text/markdown; charset=utf-8", headers=headers)
