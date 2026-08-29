from src.domain.events import EventBus, JobEvent, JobEventType
from src.domain.errors import RenderError, ErrorCode


def test_event_bus_pub_sub():
    bus = EventBus()
    events_received = []

    def _handler(event: JobEvent):
        events_received.append(event)

    bus.subscribe(_handler)

    bus.publish(JobEvent(JobEventType.STARTED, job_id="job_1"))
    bus.publish(JobEvent(JobEventType.PROGRESS, job_id="job_1", progress=0.5))
    bus.publish(JobEvent(JobEventType.COMPLETED, job_id="job_1", progress=1.0))

    assert len(events_received) == 3
    assert events_received[0].event_type == JobEventType.STARTED
    assert events_received[1].progress == 0.5
    assert events_received[2].event_type == JobEventType.COMPLETED

    # Unsubscribe
    bus.unsubscribe(_handler)
    bus.publish(JobEvent(JobEventType.STARTED, job_id="job_2"))
    assert len(events_received) == 3  # Ничего нового не добавилось
