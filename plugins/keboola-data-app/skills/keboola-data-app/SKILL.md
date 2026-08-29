---
name: keboola-data-app
description: Build Streamlit-based Keboola Data Apps with Storage Files API integration. Use when creating data applications that run on Keboola platform, need to read/write files to Keboola Storage, require OIDC user authentication via proxy headers, or build multi-step wizards with session state. Triggers: "Keboola app", "data app", "Streamlit app for Keboola", "read from Keboola Storage", "save to Keboola Files".
---

# Keboola Data App

Build Streamlit applications that integrate with Keboola Storage Files API.

## Quick Start

Minimal Keboola Data App structure:

```python
import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()

# Keboola config
KBC_URL = os.environ.get("KBC_URL", "https://connection.keboola.com")
KBC_TOKEN = os.environ.get("KBC_TOKEN", "")

def get_authenticated_user():
    """Get user from Keboola OIDC proxy or dev override."""
    dev_email = os.environ.get("DEV_USER_EMAIL")
    if dev_email:
        return dev_email
    try:
        return st.context.headers.get("X-Kbc-User-Email")
    except Exception:
        return None

st.set_page_config(page_title="My App", page_icon="📊")
user = get_authenticated_user()
st.write(f"Hello, {user or 'Guest'}!")
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `KBC_URL` or `KBC_API_URL` | Keboola connection URL |
| `KBC_TOKEN` or `KBC_API_TOKEN` | Storage API token |
| `DEV_USER_EMAIL` | Local dev override for OIDC |

## Keboola Storage Files API

### Initialize Client

```python
from kbcstorage.files import Files

def get_files_client(show_errors: bool = True):
    if not KBC_TOKEN:
        if show_errors:
            st.error("Keboola token not configured. Set KBC_TOKEN environment variable.")
        return None
    try:
        return Files(KBC_URL, KBC_TOKEN)
    except Exception as e:
        if show_errors:
            st.error(f"Failed to connect to Keboola Storage: {e}")
        return None
```

### List & Download Files by Tag

```python
def load_file_by_tags(tags: list[str], show_errors: bool = True) -> dict | None:
    """Load file that has ALL specified tags."""
    client = get_files_client(show_errors=show_errors)
    if not client:
        return None

    try:
        files_list = client.list(tags=[tags[0]], limit=1000)

        for file_info in files_list:
            file_tags = file_info.get("tags", [])
            tag_names = [t.get("name") if isinstance(t, dict) else t for t in file_tags]

            if all(tag in tag_names for tag in tags):
                file_id = file_info.get("id")
                file_name = file_info.get("name")

                with tempfile.TemporaryDirectory() as tmp_dir:
                    client.download(file_id, tmp_dir)
                    with open(os.path.join(tmp_dir, file_name), "r") as f:
                        return json.load(f)
        return None
    except Exception as e:
        if show_errors:
            st.error(f"Failed to load file from Keboola Storage: {e}")
        return None
```

### Upload File with Tags

```python
def save_file_with_tags(filename: str, data: dict, tags: list[str], show_errors: bool = True) -> bool:
    """Upload JSON file to Keboola Storage with tags."""
    client = get_files_client(show_errors=show_errors)
    if not client:
        return False

    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            local_path = os.path.join(tmp_dir, filename)

            with open(local_path, "w") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            client.upload_file(
                file_path=local_path,
                tags=tags,
                is_permanent=True,
                is_public=False
            )
            return True
    except Exception as e:
        if show_errors:
            st.error(f"Failed to save file to Keboola Storage: {e}")
        return False
```

### Delete Files by Tag

```python
def delete_files_by_tags(tags: list[str]) -> bool:
    """Delete all files matching ALL tags."""
    client = get_files_client()
    if not client:
        return False

    files_list = client.list(tags=[tags[0]], limit=1000)

    for file_info in files_list:
        file_tags = file_info.get("tags", [])
        tag_names = [t.get("name") if isinstance(t, dict) else t for t in file_tags]

        if all(tag in tag_names for tag in tags):
            client.delete(file_info.get("id"))

    return True
```

## Streamlit Patterns

### Session State for Multi-Step Wizard

```python
def init_session_state():
    if "current_step" not in st.session_state:
        st.session_state.current_step = 0
    if "answers" not in st.session_state:
        st.session_state.answers = {}
    if "submitted" not in st.session_state:
        st.session_state.submitted = False
```

### Widget State Sync Pattern

```python
def init_widget_state(widget_key: str, answer_key: str):
    """Initialize widget from answers if not set."""
    if widget_key not in st.session_state:
        st.session_state[widget_key] = st.session_state.answers.get(answer_key, "")

def sync_answer(widget_key: str, answer_key: str):
    """Sync widget value back to answers."""
    st.session_state.answers[answer_key] = st.session_state.get(widget_key, "")

# Usage
answer_key = "q1"
widget_key = "input_q1"
init_widget_state(widget_key, answer_key)

st.text_area(
    "Your answer",
    key=widget_key,
    on_change=sync_answer,
    args=(widget_key, answer_key)
)
```

### Navigation with Progress

```python
def render_progress(current: int, total: int):
    st.progress((current + 1) / total)
    st.markdown(f"Step {current + 1} of {total}")

def render_navigation(current: int, total: int):
    col1, _, col3 = st.columns([1, 1, 1])

    with col1:
        if current > 0 and st.button("← Previous"):
            st.session_state.current_step -= 1
            st.rerun()

    with col3:
        if current < total - 1:
            if st.button("Next →", type="primary"):
                st.session_state.current_step += 1
                st.rerun()
        else:
            if st.button("Submit ✓", type="primary"):
                st.session_state.submitted = True
                st.rerun()
```

## File Naming Convention

Convert email to safe filename:

```python
def email_to_filename(email: str) -> str:
    """petr@keboola.com -> petr_keboola.com.json"""
    return f"{email.replace('@', '_')}.json" if email else "anonymous.json"

def filename_to_email(filename: str) -> str:
    """petr_keboola.com.json -> petr@keboola.com"""
    name = filename.replace(".json", "")
    parts = name.split("_", 1)
    return f"{parts[0]}@{parts[1]}" if len(parts) == 2 else name
```

## Requirements

```
streamlit
python-dotenv
kbcstorage
```

## References

- For Google Sheets export integration: See [references/google_sheets.md](references/google_sheets.md)
- For advanced Streamlit patterns: See [references/streamlit_patterns.md](references/streamlit_patterns.md)
