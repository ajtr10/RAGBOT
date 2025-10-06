module.exports = {
  apps: [
    {
      name: 'ragbot-server',
      cwd: '/home/ubuntu/RAGBOT',
      script: '/home/ubuntu/RAGBOT/venv/bin/python',
      args: '-m uvicorn server.working_main:app --host 0.0.0.0 --port 8000',
      interpreter: 'none',
      env: {
        PYTHONPATH: '/home/ubuntu/RAGBOT'
      },
      error_file: '/home/ubuntu/RAGBOT/logs/server-error.log',
      out_file: '/home/ubuntu/RAGBOT/logs/server-out.log'
    },
    {
      name: 'ragbot-client',
      cwd: '/home/ubuntu/RAGBOT',
      script: '/home/ubuntu/RAGBOT/venv/bin/python',
      args: '-m streamlit run client/app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true',
      interpreter: 'none',
      env: {
        PYTHONPATH: '/home/ubuntu/RAGBOT'
      },
      error_file: '/home/ubuntu/RAGBOT/logs/client-error.log',
      out_file: '/home/ubuntu/RAGBOT/logs/client-out.log'
    }
  ]
};