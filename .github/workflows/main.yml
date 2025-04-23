name: Run VSCode with Agro Tunnel

on: [push]

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout repository
      uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.x

    - name: Install required tools
      run: |
        if [ ! -f cloudflared ]; then
          wget -q -nc https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -O cloudflared
          chmod +x cloudflared
        fi
        curl -fsSL https://code-server.dev/install.sh | sh

    - name: Start VSCode
      env:
        PORT: 10000
      run: |
        code-server --port $PORT --disable-telemetry --auth none &
    
    - name: Delay before creating tunnel
      run: sleep 10

    - name: Start Agro Tunnel
      env:
        PORT: 10000
      run: |
        while true; do
          ./cloudflared tunnel --url http://127.0.0.1:$PORT --metrics localhost:45678
        done
