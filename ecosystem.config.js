module.exports = {
  apps: [
    {
      name: 'ragbot-server',
      cwd: '/home/ubuntu/RAGBOT',
      script: '/home/ubuntu/RAGBOT/venv/bin/python',
      args: '-c "import sys; sys.path.append(\'/home/ubuntu/RAGBOT\'); from server.working_main import app; import uvicorn; uvicorn.run(app, host=\'0.0.0.0\', port=8000)"',
      interpreter: 'none'
    },
    {
      name: 'ragbot-client',
      cwd: '/home/ubuntu/RAGBOT',
      script: '/home/ubuntu/RAGBOT/venv/bin/python',
      args: '-c "import sys; sys.path.append(\'/home/ubuntu/RAGBOT\'); import streamlit; streamlit.run(\'client/app.py\', flag_options={\'server.port\': 8501, \'server.address\': \'0.0.0.0\', \'server.headless\': True})"',
      interpreter: 'none'
    }
  ]
};