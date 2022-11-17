#/bin/bash -e

function cleanup {
  docker-compose down
}

trap cleanup EXIT

echo "Installing requirements"
pip3 install -r requirements.txt
docker-compose up -d
echo "Waiting for Selenium standalone firefox to boot up"
sleep 10
python3 ./function_app.py bein.xmltv 3

echo "Script finished successfully"