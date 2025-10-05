module.exports = {
  apps: [
    {
      name: 'ragbot-server',
      cwd: '/home/ubuntu/ragbot',
      script: '/home/ubuntu/ragbot/venv/bin/uvicorn',
      args: 'server.working_main:app --host 0.0.0.0 --port 8000',
      interpreter: 'none',
      env: {
        PATH: '/home/ubuntu/ragbot/venv/bin:' + process.env.PATH,
        PYTHONPATH: '/home/ubuntu/ragbot'
      },
      error_file: '/home/ubuntu/ragbot/logs/server-error.log',
      out_file: '/home/ubuntu/ragbot/logs/server-out.log'
    },
    {
      name: 'ragbot-client',
      cwd: '/home/ubuntu/ragbot',
      script: '/home/ubuntu/ragbot/venv/bin/streamlit',
      args: 'run client/app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true',
      interpreter: 'none',
      env: {
        PATH: '/home/ubuntu/ragbot/venv/bin:' + process.env.PATH,
        PYTHONPATH: '/home/ubuntu/ragbot'
      },
      error_file: '/home/ubuntu/ragbot/logs/client-error.log',
      out_file: '/home/ubuntu/ragbot/logs/client-out.log'
    }
  ]
};