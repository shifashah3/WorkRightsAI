
  # Work Rights AI Screen

  This is a code bundle for Work Rights AI Screen. The original project is available at https://www.figma.com/design/Ao1X29oiAoTfb3Ew9J0tOU/Work-Rights-AI-Screen.

  ## Running the code

  Run `npm i` to install the frontend dependencies.

  Run `npm run dev` to start the Vite development server.

  ## Running the chatbot backend

  From the repository root, install Python dependencies:

  ```bash
  pip install -r requirements.txt
  ```

  Then start the backend server:

  ```bash
  python server.py
  ```

  The frontend will proxy requests to `http://127.0.0.1:8000/api/chat` automatically.
  