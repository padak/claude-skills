# Advanced Streamlit Patterns

## Custom CSS Styling

```python
st.markdown("""
<style>
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Progress bar color */
    .stProgress > div > div > div > div {
        background-color: #4CAF50;
    }

    /* Card container */
    .card {
        background-color: #f8f9fa;
        padding: 2rem;
        border-radius: 10px;
        margin: 1rem 0;
    }

    /* Badge */
    .badge {
        background-color: #4CAF50;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.9rem;
        display: inline-block;
    }

    /* Rounded buttons */
    .stButton > button {
        border-radius: 20px;
        padding: 0.5rem 2rem;
    }
</style>
""", unsafe_allow_html=True)
```

## Material Icons

```python
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/icon?family=Material+Icons+Outlined');
</style>
<h1>
    <span class="material-icons-outlined" style="font-size: 42px; color: #4CAF50;">assignment</span>
    My App
</h1>
""", unsafe_allow_html=True)
```

## Auto-Focus on Input

Use iframe component to focus textarea after navigation:

```python
import streamlit.components.v1 as components

focus_js = """
<script>
    (function() {
        function focusInput() {
            try {
                var doc = window.parent.document;
                var input = doc.querySelector('textarea[aria-label="Your answer"]');
                if (input) {
                    input.focus();
                    return true;
                }
            } catch(e) {}
            return false;
        }
        // Retry with delays for DOM readiness
        [50, 100, 200, 400, 600].forEach(function(delay) {
            setTimeout(focusInput, delay);
        });
    })();
</script>
"""
components.html(focus_js, height=0)
```

## Debug Mode with Query Params

```python
if st.query_params.get("debug"):
    with st.expander("Debug Info", expanded=True):
        st.write(f"**User:** {authenticated_user}")
        st.write(f"**KBC_URL:** {KBC_URL}")
        st.write(f"**KBC_TOKEN:** {'***' + KBC_TOKEN[-4:] if KBC_TOKEN else 'Not set'}")
        st.json(dict(st.context.headers))
```

## Review Page with Edit Links

```python
def render_review_page(questions: list, answers: dict):
    st.markdown("## Review Your Answers")

    for i, question in enumerate(questions):
        with st.expander(f"**Q{i+1}:** {question['title']}", expanded=True):
            answer = answers.get(f"q{i+1}", "")
            if answer:
                st.markdown(f"> {answer}")
            else:
                st.markdown("_No answer provided_")

            if st.button(f"Edit Question {i+1}", key=f"edit_{i+1}"):
                st.session_state.current_step = i
                st.session_state.show_review = False
                st.session_state.editing_from_review = True
                st.rerun()
```

## CSV Export

```python
import io

def generate_csv(data: list[dict], columns: list[str]) -> str:
    output = io.StringIO()

    # Header
    output.write(",".join(f'"{c}"' for c in columns) + "\n")

    # Rows
    for row in data:
        values = []
        for col in columns:
            val = str(row.get(col, ""))
            # Escape quotes and newlines
            val = val.replace('"', '""').replace('\n', ' ')
            values.append(f'"{val}"')
        output.write(",".join(values) + "\n")

    return output.getvalue()

# Download button
csv_data = generate_csv(data, ["col1", "col2"])
st.download_button(
    label="Download CSV",
    data=csv_data,
    file_name="export.csv",
    mime="text/csv"
)
```

## Conditional Welcome Message

```python
if st.session_state.current_step == 0:
    user_display = authenticated_user or "there"

    st.markdown(f"""
    <div style='background-color: #e8f5e9; padding: 1rem; border-radius: 10px;'>
        <strong>Hi {user_display}!</strong><br><br>
        Welcome to the application.
    </div>
    """, unsafe_allow_html=True)
```

## Question Dots Navigation

Visual indicator showing progress through questions:

```python
cols = st.columns(TOTAL_QUESTIONS)
for i, col in enumerate(cols):
    with col:
        if i == st.session_state.current_step:
            st.markdown("●")  # Current
        elif st.session_state.answers.get(f"q{i+1}"):
            st.markdown("○")  # Answered
        else:
            st.markdown("·")  # Unanswered
```

## Role-Based Views

```python
CEO_EMAIL = os.environ.get("CEO_EMAIL", "")

def is_ceo(email: str) -> bool:
    if not email or not CEO_EMAIL:
        return False
    return email.lower() == CEO_EMAIL.lower()

# In main():
if is_ceo(authenticated_user):
    render_admin_dashboard()
else:
    render_user_view()
```

## Loading Existing Data Choice

```python
def render_existing_data_choice():
    """Ask user whether to load existing data or start fresh."""
    st.markdown("""
    <div style='background-color: #fff3cd; padding: 1.5rem; border-radius: 10px; border: 1px solid #ffc107;'>
        <h3>Previous Data Found</h3>
        <p>Would you like to continue with your previous data or start fresh?</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Load Previous", type="primary"):
            st.session_state.data = st.session_state.existing_data
            st.session_state.chose_action = True
            st.rerun()

    with col2:
        if st.button("Start Fresh"):
            st.session_state.data = {}
            st.session_state.chose_action = True
            st.rerun()
```
