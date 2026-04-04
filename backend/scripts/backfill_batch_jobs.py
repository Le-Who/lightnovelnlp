import sys
import os

# Ensure backend directory is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
sys.path.append(backend_dir)

from app.db import SessionLocal  # noqa: E402
from app.models.glossary import BatchJob, BatchJobItem  # noqa: E402


def backfill_counts():
    print("Starting backfill of BatchJob counts...")
    db = SessionLocal()
    try:
        jobs = db.query(BatchJob).all()
        print(f"Found {len(jobs)} jobs to check.")

        updated_count = 0
        for job in jobs:
            # Count items directly from DB (source of truth)
            completed_count = (
                db.query(BatchJobItem)
                .filter(
                    BatchJobItem.batch_job_id == job.id,
                    BatchJobItem.status == "completed",
                )
                .count()
            )

            failed_count = (
                db.query(BatchJobItem)
                .filter(
                    BatchJobItem.batch_job_id == job.id, BatchJobItem.status == "failed"
                )
                .count()
            )

            # Calculate progress
            progress = 0
            if job.total_items > 0:
                progress = round(
                    (completed_count + failed_count) / job.total_items * 100
                )

            # Check if update is needed
            if (
                job.processed_items != completed_count
                or job.failed_items != failed_count
                or job.progress_percentage != progress
            ):
                job.processed_items = completed_count
                job.failed_items = failed_count
                job.progress_percentage = progress
                updated_count += 1
                # Commit in batches if needed, but here simple commit at end or per job

        if updated_count > 0:
            db.commit()
            print(f"Successfully updated {updated_count} jobs.")
        else:
            print("No jobs needed updating.")

    except Exception as e:
        print(f"Error during backfill: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    backfill_counts()
