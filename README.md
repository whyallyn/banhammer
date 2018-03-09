BanHammer
=========
BanHammer is a one-stop shop for banning. If you need the capability to ban, block, stop or disable something in your network _fast_, BanHammer is here to help!

About
-----
BanHammer allows security teams to ban, block, or disable:

* individual IP addresses
* IP address ranges
* subnets
* domains
* URLs
* hashes
* user accounts

BanHammer has plugins and methods for:

* Active Directory
* Bit9
* Google
* LastPass
* Palo Alto Networks (PAN)

Getting Started
---------------
Install system dependencies:

	yum install gcc libffi-devel xmlsec1 xmlsec1-openssl openldap-devel python-devel openssl-devel postgresql postgresql-devel postgresql-server

Setup Postgres:

    postgresql-setup initdb

Update `/var/lib/pgsql/data/pg_hba.conf` to allow for passwords on localhost by setting method to `md5`, then run the following:

    systemctl start postgresql
    sudo -H -u postgres bash -c 'psql -f postgres-setup.sql'

Install all required Python dependencies:

	pip install -r requirements.txt

Copy the example configurations:

	cp config.ini.example config.ini
	cp plugins.ini.example plugins.ini

Modify `config.ini` and `plugins.ini` for your environment. For testing, the defaults are fine.

Prepare the BanHammer database:

    python manage.py migrate contenttypes
    python manage.py migrate auth
    python manage.py migrate api
    python manage.py migrate authtoken
    python manage.py migrate sessions
    python manage.py migrate api

Start the BanHammer web app:

	python manage.py runserver

Navigate your browser to http://127.0.0.1:8000/web/.

Running in Production
---------------------
Creating long-lived API keys:

    python manage.py shell
    >>> from django.contrib.auth.models import User
    >>> from rest_framework.authtoken.models import Token
    >>> u = User.objects.get(username = 'joe')
    >>> Token.objects.create(user=u)
