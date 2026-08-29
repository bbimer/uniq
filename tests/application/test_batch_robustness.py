import os
import threading
import pytest
from src.domain.config.execution_policy import ExecutionPolicy
from src.domain.errors import ErrorCode
from src.app.jobs.job import Job, JobStatus
from src.app.services.batch_service import BatchService
from src.app.services.legacy_adapter import LegacyConfigAdapter


def test_batch_partial_failure_isolation(synthetic_video, tmp_path):
    """
    Проверка изоляции ошибок: ошибка в одном задании (битый путь)
    не прерывает выполнение остальных заданий в пакете.
    """
    job_ok_1 = LegacyConfigAdapter.create_job(
        in_path=synthetic_video,
        out_path=os.path.join(tmp_path, "job_1.mp4"),
        filters=["Нет фильтра"],
        zoom_p=100,
        speed_p=100,
        overlay_file=None,
        overlay_pos="Середина-Центр",
        output_format="Оригинальный",
        blur_background=False,
        preset="ultrafast"
    )

    job_bad = LegacyConfigAdapter.create_job(
        in_path="C:/non_existent_path_video_xyz.mp4",
        out_path=os.path.join(tmp_path, "job_bad.mp4"),
        filters=["Нет фильтра"],
        zoom_p=100,
        speed_p=100,
        overlay_file=None,
        overlay_pos="Середина-Центр",
        output_format="Оригинальный",
        blur_background=False,
        preset="ultrafast"
    )

    job_ok_2 = LegacyConfigAdapter.create_job(
        in_path=synthetic_video,
        out_path=os.path.join(tmp_path, "job_2.mp4"),
        filters=["Нет фильтра"],
        zoom_p=100,
        speed_p=100,
        overlay_file=None,
        overlay_pos="Середина-Центр",
        output_format="Оригинальный",
        blur_background=False,
        preset="ultrafast"
    )

    policy = ExecutionPolicy(max_concurrent_jobs=2, stop_on_first_error=False)
    batch_service = BatchService(policy=policy)

    errors_caught = []
    def _on_err(job, err):
        errors_caught.append((job.id, err.code))

    results = batch_service.execute([job_ok_1, job_bad, job_ok_2], on_job_error=_on_err)

    assert job_ok_1.status == JobStatus.COMPLETED
    assert job_bad.status == JobStatus.FAILED
    assert job_ok_2.status == JobStatus.COMPLETED

    assert len(errors_caught) == 1
    assert errors_caught[0][1] == ErrorCode.FILE_NOT_FOUND


def test_batch_cancellation(synthetic_video, tmp_path):
    """Проверка отмены всего пакета через cancel_token."""
    jobs = [
        LegacyConfigAdapter.create_job(
            in_path=synthetic_video,
            out_path=os.path.join(tmp_path, f"cancel_job_{i}.mp4"),
            filters=["Нет фильтра"],
            zoom_p=100,
            speed_p=100,
            overlay_file=None,
            overlay_pos="Середина-Центр",
            output_format="Оригинальный",
            blur_background=False,
            preset="ultrafast"
        )
        for i in range(4)
    ]

    cancel_token = threading.Event()
    cancel_token.set()  # Отменяем сразу до старта

    batch_service = BatchService(policy=ExecutionPolicy(max_concurrent_jobs=2))
    results = batch_service.execute(jobs, cancel_token=cancel_token)

    for job in results:
        assert job.status == JobStatus.CANCELLED
