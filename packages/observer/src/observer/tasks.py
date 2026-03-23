from celery import Celery
import os

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "world_ai_observer",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=60,
    worker_prefetch_multiplier=1,
)


@celery_app.task(name="observer.classify_agent")
def classify_agent(agent_data: dict) -> dict:
    from .classifier import classifier

    species_label = classifier.classify_new_agent(agent_data)

    return {
        "agent_id": agent_data.get("id"),
        "species_label": species_label,
    }


@celery_app.task(name="observer.narrate_event")
def narrate_event(event: dict) -> dict:
    from .classifier import narrator

    narration = narrator.narrate(event)

    return {
        "event_type": event.get("type"),
        "tick": event.get("tick"),
        "narration": narration,
    }


@celery_app.task(name="observer.analyze_world")
def analyze_world(world_state: dict) -> dict:
    from .classifier import analyzer

    analysis = analyzer.analyze(world_state)

    return {
        "tick": world_state.get("tick"),
        "analysis": analysis,
    }


@celery_app.task(name="observer.batch_classify")
def batch_classify(agents_data: list) -> list:
    from .classifier import classifier

    results = []
    for agent_data in agents_data:
        species_label = classifier.classify_new_agent(agent_data)
        results.append(
            {
                "agent_id": agent_data.get("id"),
                "species_label": species_label,
            }
        )

    return results
