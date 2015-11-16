Welcome to django-plans
=======================

.. image:: https://travis-ci.org/swappsco/django-plans.svg?branch=master   
   :target: https://travis-ci.org/swappsco/django-plans

.. image:: https://coveralls.io/repos/swappsco/django-plans/badge.svg?branch=master&service=github
   :target: https://coveralls.io/github/swappsco/django-plans?branch=master

.. image:: https://requires.io/github/swappsco/django-plans/requirements.svg?branch=master
     :target: https://requires.io/github/swappsco/django-plans/requirements/?branch=master
     :alt: Requirements Status

.. image:: https://badge.fury.io/py/django-plans.svg
    :target: https://badge.fury.io/py/django-plans
   
Django-plans is a pluggable app for managing pricing plans with quotas and accounts expiration. 
Features currently supported:

* multiple plans,
* support for user custom plans,
* flexible model for parametrizing plans (quota),
* customizable billing periods (plan pricing),
* order total calculation using customizable taxation policy (e.g. in EU calculating VAT based on seller/buyer countries and VIES)
* invoicing,
* account expiratons + e-mail remainders.

Documentation: https://django-plans-swapps.readthedocs.org/

Support for python 2.7 and 3.3.
We support at most 2 versions of Django at any given time: The latest LTS version and the current version. Currently support Django 1.8.

This project is a fork of https://github.com/cypreess/django-plans
