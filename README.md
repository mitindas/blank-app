# Anonymous File Drop

Upload a file without registration and receive a download link. Files are removed automatically after 96 hours.

### How to run it locally

1. Install the requirements

   ```
   $ pip install -r requirements.txt
   ```

2. Run the app

   ```
   $ streamlit run streamlit_app.py
   ```

### Optional configuration

If you want the app to show a full download URL (not just a `?file=...` link), set a base URL in Streamlit secrets:

```
BASE_URL = "https://your-app-domain.example"
```
