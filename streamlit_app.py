import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import streamlit as st

UPLOAD_DIR = Path("uploads")
META_FILE = UPLOAD_DIR / "metadata.json"
RETENTION_HOURS = 96


def load_metadata() -> dict:
    if not META_FILE.exists():
        return {}
    try:
        return json.loads(META_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def save_metadata(metadata: dict) -> None:
    META_FILE.write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def cleanup_expired(metadata: dict) -> dict:
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=RETENTION_HOURS)
    changed = False
    for file_id, info in list(metadata.items()):
        try:
            uploaded_at = datetime.fromisoformat(info["uploaded_at"])
        except (KeyError, ValueError):
            uploaded_at = cutoff - timedelta(seconds=1)
        if uploaded_at < cutoff:
            file_path = UPLOAD_DIR / file_id
            if file_path.exists():
                file_path.unlink()
            metadata.pop(file_id, None)
            changed = True
    if changed:
        save_metadata(metadata)
    return metadata


def get_query_file_id() -> str | None:
    if hasattr(st, "query_params"):
        return st.query_params.get("file")
    return st.experimental_get_query_params().get("file", [None])[0]


def build_download_link(file_id: str) -> str:
    base_url = st.secrets.get("BASE_URL") or st.session_state.get("base_url")
    if base_url:
        return f"{base_url.rstrip('/')}/{file_id}"
    return f"{file_id}"


st.set_page_config(page_title="Anonymous File Drop", page_icon=None)
st.title("Anonymous File Drop")
st.write("Upload a file and get a shareable download link. Files are removed after 96 hours.")

UPLOAD_DIR.mkdir(exist_ok=True)
metadata = cleanup_expired(load_metadata())

file_id = get_query_file_id()
if file_id:
    info = metadata.get(file_id)
    if not info:
        st.error("That file link is invalid or has expired.")
    else:
        file_path = UPLOAD_DIR / file_id
        if not file_path.exists():
            st.error("That file is missing or has expired.")
        else:
            st.subheader("Download")
            st.caption(f"Filename: {info['original_name']}")
            st.download_button(
                label="Download file",
                data=file_path.read_bytes(),
                file_name=info["original_name"],
            )

st.divider()
st.subheader("Upload")
uploaded_file = st.file_uploader("Choose a file")
if uploaded_file is not None and st.button("Upload"):
    new_id = uuid4().hex[:4]
    file_path = UPLOAD_DIR / new_id
    file_path.write_bytes(uploaded_file.getvalue())
    metadata[new_id] = {
        "original_name": uploaded_file.name,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "size_bytes": len(uploaded_file.getvalue()),
    }
    save_metadata(metadata)
    st.success("Upload complete.")
    st.write("Download link:")
    st.code(build_download_link(new_id))
