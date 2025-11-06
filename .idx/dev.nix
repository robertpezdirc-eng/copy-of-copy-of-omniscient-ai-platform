# To learn more about how to use Nix to configure your environment
# see: https://firebase.google.com/docs/studio/customize-workspace
{ pkgs, ... }: {
  # Which nixpkgs channel to use.
  channel = "stable-24.05"; # or "unstable"

  # Use https://search.nixos.org/packages to find packages
  packages = [
    pkgs.python311
    pkgs.python311Packages.pip
    pkgs.nodejs_20
    pkgs.nodePackages.npm
    pkgs.firebase-tools
    pkgs.python311Packages.pytest
    pkgs.python311Packages.pytest-mock
    pkgs.python311Packages.pytest-asyncio
    pkgs.python311Packages.pytest-cov
    pkgs.python311Packages.requests-mock
    pkgs.python311Packages.faker
    pkgs.python311Packages.fastapi
    pkgs.python311Packages.uvicorn
    pkgs.python311Packages.pydantic
    pkgs.python311Packages.python-dotenv
    pkgs.python311Packages.python-multipart
    pkgs.python311Packages.sqlalchemy
    pkgs.python311Packages.alembic
    pkgs.python311Packages.psycopg2
    pkgs.python311Packages.pymysql
    pkgs.python311Packages.pymongo
    pkgs.python311Packages.motor
    pkgs.python311Packages.redis
    pkgs.python311Packages.pyjwt
    pkgs.python311Packages.passlib
    pkgs.python311Packages.python-jose
    pkgs.python311Packages.pyotp
    pkgs.python311Packages.cryptography
    pkgs.python311Packages.stripe
    pkgs.python311Packages.google-generativeai
    pkgs.python311Packages.sendgrid
    pkgs.python311Packages.twilio
    pkgs.python311Packages.python-telegram-bot
    pkgs.python311Packages.requests
    pkgs.python311Packages.httpx
    pkgs.python311Packages.email-validator
    pkgs.python311Packages.pillow
    pkgs.python311Packages.python-magic
    pkgs.python311Packages.openai
    pkgs.python311Packages.anthropic
    pkgs.python311Packages.tensorflow
    pkgs.python311Packages.torch
    pkgs.python311Packages.torchvision
    pkgs.python311Packages.scikit-learn
    pkgs.python311Packages.pandas
    pkgs.python311Packages.numpy
    pkgs.python311Packages.scipy
    pkgs.python311Packages.prophet
    pkgs.python311Packages.statsmodels
    pkgs.python311Packages.spacy
    pkgs.python311Packages.transformers
    pkgs.python311Packages.sentence-transformers
    pkgs.python311Packages.nltk
    pkgs.python311Packages.faiss
    pkgs.python311Packages.chromadb
    pkgs.python311Packages.pyod
    pkgs.python311Packages.neo4j
    pkgs.python311Packages.py2neo
    pkgs.python311Packages.keras
    pkgs.python311Packages.xgboost
    pkgs.python311Packages.lightgbm
    pkgs.python311Packages.opencv
    pkgs.python311Packages.sentry-sdk
    pkgs.python311Packages.prometheus-client
    pkgs.python311Packages.celery
    pkgs.python311Packages.kombu
    pkgs.python311Packages.opentelemetry-api
    pkgs.python311Packages.opentelemetry-sdk
    pkgs.python311Packages.opentelemetry-instrumentation-fastapi
    pkgs.python311Packages.opentelemetry-instrumentation-asgi
    pkgs.python311Packages.opentelemetry-exporter-jaeger
  ];

  # Sets environment variables in the workspace
  env = {};
  idx = {
    # Search for the extensions you want on https://open-vsx.org/ and use "publisher.id"
    extensions = [
      # "vscodevim.vim"
    ];

    # Enable previews
    previews = {
      enable = true;
      previews = {
        # web = {
        #   # Example: run "npm run dev" with PORT set to IDX's defined port for previews,
        #   # and show it in IDX's web preview panel
        #   command = ["npm" "run" "dev"];
        #   manager = "web";
        #   env = {
        #     # Environment variables to set for your server
        #     PORT = "$PORT";
        #   };
        # };
      };
    };

    # Workspace lifecycle hooks
    workspace = {
      # Runs when a workspace is first created
      onCreate = {
        install-py-deps = '''
          pip install -r ai-worker/requirements.txt
          pip install -r backend/functions/requirements.txt
          pip install -r gateway/requirements.txt
          pip install -r omni-enterprise-ultra-max/backend/requirements.txt
          pip install -r omni-enterprise-ultra-max/gateway/requirements.txt
        ''';
        install-js-deps = '''
          (cd backend && npm install)
          (cd backend/functions && npm install)
          (cd customer-portal && npm install)
          (cd frontend && npm install)
          (cd mobile && npm install)
          (cd web-dashboard && npm install)
        ''';
      };
      # Runs when the workspace is (re)started
      onStart = {
        # Example: start a background task to watch and re-build backend code
        # watch-backend = "npm run watch-backend";
      };
    };
  };
}