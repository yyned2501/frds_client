echo starting

pip install --upgrade pip -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host=mirrors.aliyun.com >/dev/null 2>&1
echo "pip updated"

pip install -r requirements.txt -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host=mirrors.aliyun.com --upgrade >/dev/null 2>&1
echo "requirements updated"

if [ ! -d logs ]; then
  mkdir logs
fi

git config --global --add safe.directory /app

supervisord -c supervisord.conf -n