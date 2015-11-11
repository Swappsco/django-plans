Installation
============

Installing module code
------------------------

You can install with pip:

.. code-block:: bash

    $ pip install django-plans


For integration instruction please see section  :doc:`integration`.



Running example project
-----------------------

Clone git repository to your current directory:

.. code-block:: bash

    $ git clone git@github.com:swappsco/django-plans.git



Optionally create virtual environment and get required packages to run example project:

.. code-block:: bash

    $ cd django-plans/demo/
    $ pip install -r requirements.txt


Initialize example project database:

.. code-block:: bash

    $ python manage.py migrate


Initial sample data will be loaded automatically.


Start development web server:

.. code-block:: bash

    $ python manage.py runserver

Visit http://localhost:8000/