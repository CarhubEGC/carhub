FROM python:3.13-slim

WORKDIR /srv
RUN pip install --no-cache-dir Flask==3.1.0 SQLAlchemy==2.0.37 PyMySQL==1.1.1
COPY app.py database.py routes.py ./fakenodo/

USER nobody
EXPOSE 5000
CMD ["python", "-m", "flask", "--app", "fakenodo.app", "run", "--host", "0.0.0.0"]
