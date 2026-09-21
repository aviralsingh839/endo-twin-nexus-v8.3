# Database Architecture

Existing local-first database remains authoritative until a migration is proven. Core entities include patient, measurement, signal, feature, baseline, timeline, symptoms, clinical observations, imaging, annotations, models/model runs, predictions, reports, audit, provenance and device sessions.

Every patient-scoped record must carry a patient identifier and queries must enforce that scope at the data/service layer.

SQLAlchemy/Alembic are the staged target for structured ORM + migration support. Do not destroy or silently rewrite existing data.
