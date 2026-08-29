import threading
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Callable, Optional
from src.domain.config.execution_policy import ExecutionPolicy
from src.domain.errors import RenderError, ErrorCode
from src.domain.events import JobEvent, JobEventType, EventBus
from src.app.jobs.job import Job, JobStatus
from src.app.services.render_service import RenderService

logger = logging.getLogger(__name__)


class BatchService:
    """
    Application-сервис для параллельного выполнения очереди задач (Job Queue)
    с единой шиной событий EventBus, политикой исполнения ExecutionPolicy и изоляцией ошибок.
    """

    def __init__(
        self,
        render_service: Optional[RenderService] = None,
        policy: Optional[ExecutionPolicy] = None,
        event_bus: Optional[EventBus] = None
    ):
        self.render_service = render_service or RenderService()
        self.policy = policy or ExecutionPolicy()
        self.event_bus = event_bus or EventBus()

    def execute(
        self,
        jobs: List[Job],
        cancel_token: Optional[threading.Event] = None,
        event_listener: Optional[Callable[[JobEvent], None]] = None,
        # Сохраняем legacy callbacks для совместимости
        on_job_start: Optional[Callable[[Job], None]] = None,
        on_job_progress: Optional[Callable[[Job, float], None]] = None,
        on_job_done: Optional[Callable[[Job], None]] = None,
        on_job_error: Optional[Callable[[Job, RenderError], None]] = None,
    ) -> List[Job]:
        """
        Выполняет список задач. Публикует события через EventBus и опциональный listener.
        """
        if event_listener:
            self.event_bus.subscribe(event_listener)

        batch_cancel = cancel_token or threading.Event()

        def _publish(event: JobEvent):
            self.event_bus.publish(event)

        def _worker(job: Job) -> Job:
            if batch_cancel.is_set():
                job.status = JobStatus.CANCELLED
                job.error_message = "Пакетная обработка была отменена"
                _publish(JobEvent(JobEventType.CANCELLED, job.id, message=job.error_message))
                return job

            logger.info("job=%s started encoder=%s", job.id, job.encoder.backend.value)
            _publish(JobEvent(JobEventType.STARTED, job.id, progress=0.0))
            if on_job_start:
                on_job_start(job)

            def _progress(p: float):
                _publish(JobEvent(JobEventType.PROGRESS, job.id, progress=p))
                if on_job_progress:
                    on_job_progress(job, p)

            try:
                self.render_service.render(job, cancel_token=batch_cancel, on_progress=_progress)
                logger.info("job=%s completed", job.id)
                _publish(JobEvent(JobEventType.COMPLETED, job.id, progress=1.0))
                if on_job_done:
                    on_job_done(job)
            except RenderError as re:
                logger.error("job=%s failed code=%s message=%s", job.id, re.code.value, re.message)
                _publish(JobEvent(JobEventType.FAILED, job.id, error=re, message=re.message))
                if on_job_error:
                    on_job_error(job, re)
                if self.policy.stop_on_first_error:
                    batch_cancel.set()
            except Exception as ex:
                err = RenderError(ErrorCode.UNKNOWN_ERROR, str(ex), job_id=job.id, cause=ex)
                logger.error("job=%s unexpected error: %s", job.id, ex)
                _publish(JobEvent(JobEventType.FAILED, job.id, error=err, message=str(ex)))
                if on_job_error:
                    on_job_error(job, err)
                if self.policy.stop_on_first_error:
                    batch_cancel.set()

            return job

        try:
            with ThreadPoolExecutor(max_workers=self.policy.max_concurrent_jobs) as executor:
                futures = [executor.submit(_worker, job) for job in jobs]
                for f in as_completed(futures):
                    try:
                        f.result()
                    except Exception:
                        pass
        finally:
            _publish(JobEvent(JobEventType.BATCH_COMPLETED, "batch_all", progress=1.0))
            if event_listener:
                self.event_bus.unsubscribe(event_listener)

        return jobs
