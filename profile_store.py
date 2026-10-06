"""Transactional SQLite profile storage, with non-destructive legacy JSON import."""

import json
import logging
import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


def now_iso():
    return datetime.now(timezone.utc).isoformat()


class ProfileStore:
    def __init__(self, storage_dir="profiles"):
        self.storage_dir = str(Path(__file__).resolve().parent / storage_dir)
        Path(self.storage_dir).mkdir(parents=True, exist_ok=True)
        self.database_path = Path(self.storage_dir) / "pathfinder.sqlite3"
        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("CREATE TABLE IF NOT EXISTS profiles (id TEXT PRIMARY KEY, data TEXT NOT NULL)")
            connection.execute("CREATE TABLE IF NOT EXISTS legacy_imports (filename TEXT PRIMARY KEY)")
        self._import_legacy_profiles()

    @staticmethod
    def _id(profile_id):
        try:
            return str(uuid.UUID(str(profile_id)))
        except (ValueError, TypeError, AttributeError) as exc:
            raise ValueError("Invalid profile ID") from exc

    @contextmanager
    def _connect(self, write=False):
        connection = sqlite3.connect(self.database_path, timeout=15)
        try:
            if write:
                connection.execute("BEGIN IMMEDIATE")
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _import_legacy_profiles(self):
        # Keep original files as backups. An import ledger prevents deleted
        # profiles from reappearing when the application is restarted.
        for path in Path(self.storage_dir).glob("*.json"):
            try:
                profile_id = self._id(path.stem)
                with self._connect(write=True) as connection:
                    imported = connection.execute("SELECT 1 FROM legacy_imports WHERE filename=?", (path.name,)).fetchone()
                    if imported:
                        row = connection.execute("SELECT data FROM profiles WHERE id=?", (profile_id,)).fetchone()
                        if not row:
                            continue
                        # Preserve assessments saved by an older server that was
                        # still running during an upgrade; never overwrite tokens.
                        current = json.loads(row[0])
                        legacy = json.loads(path.read_text(encoding="utf-8"))
                        history = current.setdefault("assessments", [])
                        known = {item.get("id") or json.dumps(item, sort_keys=True) for item in history}
                        additions = [item for item in legacy.get("assessments", [])
                                     if (item.get("id") or json.dumps(item, sort_keys=True)) not in known]
                        if additions:
                            history.extend(additions)
                            connection.execute("UPDATE profiles SET data=? WHERE id=?", (json.dumps(current), profile_id))
                        continue
                    data = json.loads(path.read_text(encoding="utf-8"))
                    if not isinstance(data, dict):
                        raise ValueError("Profile must be an object")
                    data["id"] = profile_id
                    connection.execute("INSERT OR IGNORE INTO profiles VALUES (?, ?)", (profile_id, json.dumps(data)))
                    connection.execute("INSERT INTO legacy_imports VALUES (?)", (path.name,))
            except (ValueError, OSError, sqlite3.Error):
                logger.warning("Skipped unreadable legacy profile file %s", path.name)

    def create_profile(self, profile_data):
        data = dict(profile_data)
        profile_id = self._id(data.get("id") or uuid.uuid4())
        timestamp = now_iso()
        data.update(id=profile_id, created_at=timestamp, updated_at=timestamp)
        data.setdefault("assessments", [])
        if not self._save_profile(profile_id, data):
            raise OSError("Failed to save profile")
        return profile_id

    def get_profile(self, profile_id):
        profile_id = self._id(profile_id)
        with self._connect() as connection:
            row = connection.execute("SELECT data FROM profiles WHERE id=?", (profile_id,)).fetchone()
        return json.loads(row[0]) if row else None

    def update_profile(self, profile_id, profile_data):
        profile_id = self._id(profile_id)
        with self._connect(write=True) as connection:
            row = connection.execute("SELECT data FROM profiles WHERE id=?", (profile_id,)).fetchone()
            if not row:
                return False
            data = {**json.loads(row[0]), **profile_data, "id": profile_id, "updated_at": now_iso()}
            connection.execute("UPDATE profiles SET data=? WHERE id=?", (json.dumps(data), profile_id))
        return True

    def delete_profile(self, profile_id):
        profile_id = self._id(profile_id)
        with self._connect(write=True) as connection:
            deleted = connection.execute("DELETE FROM profiles WHERE id=?", (profile_id,)).rowcount > 0
        # Remove the corresponding legacy backup too when deletion was explicitly requested.
        if deleted:
            legacy = Path(self.storage_dir) / f"{profile_id}.json"
            legacy.unlink(missing_ok=True)
        return deleted

    def list_profiles(self):
        with self._connect() as connection:
            records = [json.loads(row[0]) for row in connection.execute("SELECT data FROM profiles")]
        fields = ("id", "created_at", "updated_at", "last_assessment_date", "recent_recommendation")
        return sorted(({key: profile.get(key) for key in fields} for profile in records),
                      key=lambda item: item.get("updated_at") or "", reverse=True)

    def add_assessment(self, profile_id, assessment_data):
        profile_id = self._id(profile_id)
        assessment = dict(assessment_data)
        assessment["id"] = assessment.get("id") or str(uuid.uuid4())
        assessment["timestamp"] = now_iso()
        with self._connect(write=True) as connection:
            row = connection.execute("SELECT data FROM profiles WHERE id=?", (profile_id,)).fetchone()
            if not row:
                return False
            profile = json.loads(row[0])
            history = profile.setdefault("assessments", [])
            if any(item.get("id") == assessment["id"] for item in history):
                return True
            history.append(assessment)
            profile.update(last_assessment_date=assessment["timestamp"],
                           recent_recommendation=assessment.get("recommended_career"), updated_at=now_iso())
            connection.execute("UPDATE profiles SET data=? WHERE id=?", (json.dumps(profile), profile_id))
        return True

    def get_assessment_history(self, profile_id):
        profile = self.get_profile(profile_id)
        return sorted((profile or {}).get("assessments", []),
                      key=lambda assessment: assessment.get("timestamp", ""), reverse=True)

    def _save_profile(self, profile_id, profile_data):
        profile_id = self._id(profile_id)
        try:
            with self._connect(write=True) as connection:
                connection.execute("INSERT INTO profiles VALUES (?, ?) ON CONFLICT(id) DO UPDATE SET data=excluded.data",
                                   (profile_id, json.dumps(profile_data)))
            return True
        except (sqlite3.Error, TypeError, ValueError):
            logger.exception("Unable to persist profile")
            return False


profile_store = ProfileStore(os.getenv("PROFILE_STORAGE_DIR", "profiles"))

# Backwards-compatible helpers for scripts.
create_profile = profile_store.create_profile
get_profile = profile_store.get_profile
update_profile = profile_store.update_profile
delete_profile = profile_store.delete_profile
list_profiles = profile_store.list_profiles
add_assessment = profile_store.add_assessment
get_assessment_history = profile_store.get_assessment_history
