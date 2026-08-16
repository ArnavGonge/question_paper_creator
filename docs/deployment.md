# Deployment

## Streamlit Community Cloud

1. Push the repository to GitHub.
2. Create a Streamlit Community Cloud app from the repository.
3. Set the main file path to `app.py`.
4. Streamlit Cloud installs `requirements.txt`, including the local `src/qpc` package via `-e .`.
5. Add secrets:

```toml
APP_PASSWORD = "client-password"
OPENAI_API_KEY = "real-openai-key"
OPENAI_MODEL = "gpt-4.1-mini"
```

6. Deploy the app.
7. Share the Streamlit app URL and password with the client.

## Render Or Railway

Use this route when stronger privacy or operational control is needed. Configure the same environment variables as secrets and run:

```bash
streamlit run app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true
```

## Operational Notes

- Rotate `APP_PASSWORD` if the URL is shared beyond the intended client.
- Track OpenAI API usage in the OpenAI dashboard.
- Do not commit `.streamlit/secrets.toml`.
- The app is session-based and does not preserve generated papers.
