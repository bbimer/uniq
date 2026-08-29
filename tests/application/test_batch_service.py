import os
import pytest
from src.domain.config.execution_policy import ExecutionPolicy
from src.app.jobs.job import Job, JobStatus
from src.app.services.batch_service import BatchService
from src.app.services.legacy_adapter import LegacyConfigAdapter


def test_batch_service_execution(synthetic_video, tmp_path):
    jobs = []
    for i in range(2):
        out_path = os.path.join(tmp_path, f"batch_out_{i}.mp4")
        job = LegacyConfigAdapter.create_job(
            in_path=synthetic_video,
            out_path=out_path,
            filters=["Нет фильтра"],
            zoom_p=100,
            speed_p=100,
            overlay_file=None,
            overlay_pos="Середина-Центр",
            output_format="Оригинальный",
            blur_background=False,
            mute_audio=False,
            strip_metadata=True,
            preset="ultrafast"
        )
        jobs.append(job)

    batch_service = BatchService(policy=ExecutionPolicy(max_concurrent_jobs=2))
    completed_jobs = batch_service.execute(jobs)

    assert len(completed_jobs) == 2
    for job in completed_jobs:
        assert job.status == JobStatus.COMPLETED
        assert os.path.exists(job.target_path)
        assert os.path.getsize(job.target_path) > 0
