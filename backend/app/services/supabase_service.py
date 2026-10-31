import os
import re
import json
import uuid
from typing import Dict, Any, Optional, List, Tuple
from app.core.config import settings

class SupabaseService:
    """
    Supabase client and service abstraction.
    Handles Supabase Auth, persistent database operations (profiles, query_history, uploaded_datasets),
    and private Supabase Storage buckets ('private-datasets').
    Provides graceful fallback when Supabase credentials are not configured.
    """
    _client = None

    @classmethod
    def is_configured(cls) -> bool:
        return bool(settings.SUPABASE_URL and settings.SUPABASE_KEY and 
                    "supabase.co" in settings.SUPABASE_URL and
                    settings.SUPABASE_KEY != "your_supabase_anon_key_here")

    @classmethod
    def get_client(cls):
        if not cls.is_configured():
            return None
        if cls._client is None:
            try:
                from supabase import create_client, Client
                cls._client = create_client(
                    settings.SUPABASE_URL,
                    settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_KEY
                )
            except Exception as e:
                print(f"Warning: Failed to initialize Supabase client: {e}")
                return None
        return cls._client

    # ── Auth Operations ──────────────────────────────────────────────────────────

    @classmethod
    def sign_up(cls, email: str, password: str, full_name: str) -> Dict[str, Any]:
        """Registers a user via Supabase Auth."""
        client = cls.get_client()
        if not client:
            raise RuntimeError("Supabase credentials are not configured.")
        
        res = client.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {"full_name": full_name}
            }
        })
        if not res.user:
            raise ValueError("Registration failed.")
        
        user_id = str(res.user.id)
        token = res.session.access_token if res.session else None
        
        # Ensure profile exists in public.users
        try:
            client.table("users").upsert({
                "id": user_id,
                "email": email,
                "full_name": full_name
            }).execute()
        except Exception:
            pass # trigger handle_new_user might already handle this

        return {
            "user_id": user_id,
            "email": email,
            "full_name": full_name,
            "access_token": token
        }

    @classmethod
    def sign_in(cls, email: str, password: str) -> Dict[str, Any]:
        """Authenticates user with Supabase Auth."""
        client = cls.get_client()
        if not client:
            raise RuntimeError("Supabase credentials are not configured.")

        res = client.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        if not res.user or not res.session:
            raise ValueError("Invalid email or password.")

        user_id = str(res.user.id)
        full_name = (res.user.user_metadata or {}).get("full_name") or email.split("@")[0]
        
        return {
            "user_id": user_id,
            "email": res.user.email,
            "full_name": full_name,
            "access_token": res.session.access_token
        }

    @classmethod
    def verify_token(cls, token: str) -> Optional[Dict[str, Any]]:
        """Verifies Supabase JWT access token and returns user dictionary."""
        client = cls.get_client()
        if not client:
            return None

        try:
            user_res = client.auth.get_user(token)
            if user_res and user_res.user:
                u = user_res.user
                full_name = (u.user_metadata or {}).get("full_name") or u.email.split("@")[0]
                return {
                    "id": str(u.id),
                    "email": u.email,
                    "full_name": full_name
                }
        except Exception as e:
            # Token invalid or expired
            return None
        return None

    # ── Query History Operations ────────────────────────────────────────────────

    @classmethod
    def record_query(
        cls,
        user_id: str,
        natural_query: str,
        generated_sql: str,
        executed: bool = False,
        status: str = "generated",
        execution_time_ms: Optional[float] = None,
        row_count: Optional[int] = None,
        error_message: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        client = cls.get_client()
        if not client:
            return None
        try:
            data = {
                "user_id": user_id,
                "natural_query": natural_query,
                "generated_sql": generated_sql,
                "executed": executed,
                "status": status,
                "execution_time_ms": execution_time_ms,
                "row_count": row_count,
                "error_message": error_message
            }
            res = client.table("query_history").insert(data).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]
        except Exception as e:
            print(f"Warning: Failed to persist query history to Supabase: {e}")
        return None

    @classmethod
    def get_user_history(cls, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        client = cls.get_client()
        if not client:
            return []
        try:
            res = client.table("query_history") \
                .select("*") \
                .eq("user_id", user_id) \
                .order("created_at", desc=True) \
                .limit(limit) \
                .execute()
            return res.data or []
        except Exception as e:
            print(f"Warning: Failed to fetch query history from Supabase: {e}")
            return []

    @classmethod
    def clear_user_history(cls, user_id: str) -> int:
        client = cls.get_client()
        if not client:
            return 0
        try:
            res = client.table("query_history").delete().eq("user_id", user_id).execute()
            return len(res.data) if res.data else 0
        except Exception as e:
            print(f"Warning: Failed to clear query history from Supabase: {e}")
            return 0

    # ── Uploaded Datasets & Storage Operations ──────────────────────────────────

    @classmethod
    def upload_private_file(cls, user_id: str, filename: str, file_bytes: bytes) -> Optional[str]:
        """Uploads private file to Supabase Storage bucket 'private-datasets'."""
        client = cls.get_client()
        if not client:
            return None
        try:
            bucket_name = settings.SUPABASE_STORAGE_BUCKET
            file_uuid = str(uuid.uuid4())
            clean_filename = re.sub(r"[^a-zA-Z0-9_\.-]", "_", filename)
            storage_path = f"{user_id}/{file_uuid}_{clean_filename}"
            
            client.storage.from_(bucket_name).upload(
                path=storage_path,
                file=file_bytes,
                file_options={"cache-control": "3600", "upsert": "true"}
            )
            return storage_path
        except Exception as e:
            print(f"Warning: Failed to upload file to Supabase Storage: {e}")
            return None

    @classmethod
    def download_private_file(cls, storage_path: str) -> Optional[bytes]:
        """Downloads private file bytes from Supabase Storage."""
        client = cls.get_client()
        if not client:
            return None
        try:
            bucket_name = settings.SUPABASE_STORAGE_BUCKET
            return client.storage.from_(bucket_name).download(storage_path)
        except Exception as e:
            print(f"Warning: Failed to download file from Supabase Storage: {e}")
            return None

    @classmethod
    def delete_private_file(cls, storage_path: str) -> bool:
        """Deletes private file from Supabase Storage."""
        client = cls.get_client()
        if not client:
            return False
        try:
            bucket_name = settings.SUPABASE_STORAGE_BUCKET
            client.storage.from_(bucket_name).remove([storage_path])
            return True
        except Exception as e:
            print(f"Warning: Failed to delete file from Supabase Storage: {e}")
            return False

