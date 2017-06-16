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

    $ cd django-plans
    $ pip install -r demo/requirements.txt
    $ pip install -e .


Initialize example project database:

.. code-block:: bash
	$ cd django-plans/demo/
    $ python manage.py migrate


Initial sample data will be loaded automatically.


Start development web server:

.. code-block:: bash

    $ python manage.py runserver

Visit http://localhost:8000/

To implement a development environment with the development package and the chance to view the changes while they are made use:

.. code-block:: bash

    $ cd django-plans/demo/
    $ pip install -e ../plans

This should install the development package and it will update each time you incorporate some changes to the project.

For the invoice generation we use wkhtmltopdf if it is installed, or return
a plain html if it is not.
You can install wkhtmltopdf on ubuntu with:

.. code-block:: bash

    $ sudo apt-get install wkhtmltopdf
