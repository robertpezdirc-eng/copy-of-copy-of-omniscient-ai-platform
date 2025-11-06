# A/B Testing Service

This directory contains the in-memory A/B testing service used by the Advanced AI routes.

## Overview

- Service: `ABTestingService` (`backend/services/advanced_ai/ab_testing.py`)
- API routes: exposed via `backend/routes/advanced_ai_routes.py` under the prefix
  `/api/v1/advanced-ai`.
- Storage: In-memory only (per-process). Suitable for experimentation and unit tests.
- Concurrency: Writes are guarded with an `asyncio.Lock`.

## REST API

All endpoints are nested under `/api/v1/advanced-ai`.

- Create experiment
  - POST `/experiments`
  - Body:
    ```json
    {"name": "cta-test", "variants": ["A", "B"], "primary_metric": "conversion_rate", "owner": "growth"}
    ```

- Record event
  - POST `/experiments/{experiment_id}/events`
  - Body:
    ```json
    {"variant": "A", "event_type": "impression"}
    ```
    or
    ```json
    {"variant": "B", "event_type": "conversion", "value": 12.5}
    ```

- Finalize experiment
  - POST `/experiments/{experiment_id}/finalize`
  - Body:
    ```json
    {"winning_variant": "B", "summary": "Variant B outperformed A by 15%"}
    ```

- Get experiment
  - GET `/experiments/{experiment_id}`

## Notes

- On creation, all variants are included in the response with zeroed metrics.
- After finalization, additional events are ignored and metrics remain unchanged.
- Responses are deterministic and sorted by highest conversion rate.
