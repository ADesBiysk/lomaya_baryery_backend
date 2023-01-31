from http import HTTPStatus

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from fastapi_restful.cbv import cbv

from src.core.services.analytics_service import AnaliticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@cbv(router)
class AnalyticsCBV:
    analitics_service: AnaliticsService = Depends()

    @router.get(
        "/total",
        response_class=StreamingResponse,
        status_code=HTTPStatus.OK,
        summary="Формирование полного отчёта",
    )
    async def generate_full_report(
        self,
    ) -> StreamingResponse:
        """Формирует excel файл со всеми отчётами."""
        return await self.analitics_service.generate_full_report()

    @router.get(
        "/tasks",
        response_class=StreamingResponse,
        status_code=HTTPStatus.OK,
        summary="Формирование отчёта c задачами",
    )
    async def generate_task_report(self) -> StreamingResponse:
        """
        Формирует отчёт с общей статистикой выполнения задач во всех сменахм.

        Содержит:
        - cписок всех заданий;
        - общее количество принятых/отклонённых/не предоставленных отчётов по каждому заданию.
        """
        return await self.analitics_service.generate_task_report()
