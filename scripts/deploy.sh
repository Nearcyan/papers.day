#!/bin/sh
BASEPATH=/var/www2/papers.day

echo "Not compiling CSS!"
source $BASEPATH/env/bin/activate

echo "Updating from requirements.txt..."
cd $BASEPATH
python3 -m pip install -r ./requirements.txt

# Static files
echo "Collecting static files..."
cd $BASEPATH
python3 manage.py collectstatic --noinput

# DB migrations
echo "Applying migrations..."
cd $BASEPATH
python3 manage.py migrate

echo "Restarting uWSGI..."
sudo service uwsgi2 restart

exit 0
