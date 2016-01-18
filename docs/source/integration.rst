Integration
===========

This section describes step by step integration of django-plans with your application.


Enable plans application in django
----------------------------------

Add this app to your ``INSTALLED_APPS`` in your settings file::

    INSTALLED_APPS += ('plans', 'ordered_model',)

.. note::
    
    The app 'ordered_model' is required to display the assets used in the django admin to manage the plan model ordering

You should also define all other variables in ``settings.py`` marked as **required**.
They are described in detail in section :doc:`settings`.

Don't forget to run::

    $ python manage.py migrate

Add django-plans urls
---------------------
Add django-plans urls to your URL general configuration::

    add url(r'^', include('plans.urls')),

The basic django-plans urls are::

    http://localhost:8000/pricing/
    http://localhost:8000/account/
    http://localhost:8000/upgrade/
    http://localhost:8000/order/
    http://localhost:8000/billing/

.. note::

    To access all the django-plans urls, as well as their names, access plans/urls.py file in the repository

Enable context processor
-------------------------
Section :doc:`templating` describes a very helpful context processor that you can enable by adding it to the TEMPLATE options::

        'plans.context_processors.account_status'


Send signal when user account is fully activated
------------------------------------------------

You need to explicitly tell django-plans that user has fully activated account. This can vary depending on your setup, so you may want to do this on email confirmation or in sign up if the confirmation is optional or disabled. django-plans provides a special signal that it listens to::

    from plans.signals import activate_user_plan
    activate_user_plan.send(sender=None, user=user)

You should send this signal providing ``user`` argument as an object of ``auth.User`` or a subclass of ``AbstractUser`` or ``AbstractBaseUser``. django-plans will use this information to initialize plan for this user, i.e. set account expiration date and will mark the default plan as active for this account.

.. note::

    If you use django-registration app for managing user registration process,
    you are done. django-plans automagically integrates with this app
    (if it is available) and will activate user plan when django-registration
    send it's signal after account activation.
