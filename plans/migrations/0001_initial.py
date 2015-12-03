# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from decimal import Decimal
import django_countries.fields
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BillingInfo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('tax_number', models.CharField(db_index=True, max_length=200, verbose_name='VAT ID', blank=True)),
                ('name', models.CharField(max_length=200, verbose_name='name', db_index=True)),
                ('street', models.CharField(max_length=200, verbose_name='street')),
                ('zipcode', models.CharField(max_length=200, verbose_name='zip code')),
                ('city', models.CharField(max_length=200, verbose_name='city')),
                ('country', django_countries.fields.CountryField(max_length=2, verbose_name='country')),
                ('shipping_name', models.CharField(help_text='optional', max_length=200, verbose_name='name (shipping)', blank=True)),
                ('shipping_street', models.CharField(help_text='optional', max_length=200, verbose_name='street (shipping)', blank=True)),
                ('shipping_zipcode', models.CharField(help_text='optional', max_length=200, verbose_name='zip code (shipping)', blank=True)),
                ('shipping_city', models.CharField(help_text='optional', max_length=200, verbose_name='city (shipping)', blank=True)),
                ('user', models.OneToOneField(verbose_name='user', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Billing info',
                'verbose_name_plural': 'Billing infos',
            },
        ),
        migrations.CreateModel(
            name='Invoice',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('number', models.IntegerField(db_index=True)),
                ('full_number', models.CharField(max_length=200)),
                ('type', models.IntegerField(default=1, db_index=True, choices=[(1, 'Invoice'), (2, 'Invoice Duplicate'), (3, 'Order confirmation')])),
                ('issued', models.DateField(db_index=True)),
                ('issued_duplicate', models.DateField(db_index=True, null=True, blank=True)),
                ('selling_date', models.DateField(db_index=True, null=True, blank=True)),
                ('payment_date', models.DateField(db_index=True)),
                ('unit_price_net', models.DecimalField(max_digits=7, decimal_places=2)),
                ('quantity', models.IntegerField(default=1)),
                ('total_net', models.DecimalField(max_digits=7, decimal_places=2)),
                ('total', models.DecimalField(max_digits=7, decimal_places=2)),
                ('tax_total', models.DecimalField(max_digits=7, decimal_places=2)),
                ('tax', models.DecimalField(db_index=True, null=True, max_digits=4, decimal_places=2, blank=True)),
                ('rebate', models.DecimalField(default=Decimal('0'), max_digits=4, decimal_places=2)),
                ('currency', models.CharField(default='EUR', max_length=3)),
                ('item_description', models.CharField(max_length=200)),
                ('buyer_name', models.CharField(max_length=200, verbose_name='Name')),
                ('buyer_street', models.CharField(max_length=200, verbose_name='Street')),
                ('buyer_zipcode', models.CharField(max_length=200, verbose_name='Zip code')),
                ('buyer_city', models.CharField(max_length=200, verbose_name='City')),
                ('buyer_country', django_countries.fields.CountryField(default='PL', max_length=2, verbose_name='Country')),
                ('buyer_tax_number', models.CharField(max_length=200, verbose_name='TAX/VAT number', blank=True)),
                ('shipping_name', models.CharField(max_length=200, verbose_name='Name')),
                ('shipping_street', models.CharField(max_length=200, verbose_name='Street')),
                ('shipping_zipcode', models.CharField(max_length=200, verbose_name='Zip code')),
                ('shipping_city', models.CharField(max_length=200, verbose_name='City')),
                ('shipping_country', django_countries.fields.CountryField(default='PL', max_length=2, verbose_name='Country')),
                ('require_shipment', models.BooleanField(default=False, db_index=True)),
                ('issuer_name', models.CharField(max_length=200, verbose_name='Name')),
                ('issuer_street', models.CharField(max_length=200, verbose_name='Street')),
                ('issuer_zipcode', models.CharField(max_length=200, verbose_name='Zip code')),
                ('issuer_city', models.CharField(max_length=200, verbose_name='City')),
                ('issuer_country', django_countries.fields.CountryField(default='PL', max_length=2, verbose_name='Country')),
                ('issuer_tax_number', models.CharField(max_length=200, verbose_name='TAX/VAT number', blank=True)),
            ],
            options={
                'verbose_name': 'Invoice',
                'verbose_name_plural': 'Invoices',
            },
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('flat_name', models.CharField(max_length=200, null=True, blank=True)),
                ('created', models.DateTimeField(verbose_name='created', db_index=True)),
                ('completed', models.DateTimeField(db_index=True, null=True, verbose_name='completed', blank=True)),
                ('amount', models.DecimalField(verbose_name='amount', max_digits=7, decimal_places=2, db_index=True)),
                ('tax', models.DecimalField(decimal_places=2, max_digits=4, blank=True, null=True, verbose_name='tax', db_index=True)),
                ('currency', models.CharField(default='EUR', max_length=3, verbose_name='currency')),
                ('status', models.IntegerField(default=1, verbose_name='status', choices=[(1, 'new'), (2, 'completed'), (3, 'not valid'), (4, 'canceled'), (5, 'returned')])),
            ],
            options={
                'ordering': ('-created',),
                'verbose_name': 'Order',
                'verbose_name_plural': 'Orders',
            },
        ),
        migrations.CreateModel(
            name='Plan',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.PositiveIntegerField(editable=False, db_index=True)),
                ('name', models.CharField(max_length=100, verbose_name='name')),
                ('description', models.TextField(verbose_name='description', blank=True)),
                ('default', models.BooleanField(default=False, db_index=True)),
                ('available', models.BooleanField(default=False, help_text='Is still available for purchase', db_index=True, verbose_name='available')),
                ('visible', models.BooleanField(default=True, help_text='Is visible in current offer', db_index=True, verbose_name='visible')),
                ('created', models.DateTimeField(verbose_name='created', db_index=True)),
                ('url', models.CharField(help_text='Optional link to page with more information (for clickable pricing table headers)', max_length=200, blank=True)),
                ('customized', models.ForeignKey(verbose_name='customized', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ('order',),
                'verbose_name': 'Plan',
                'verbose_name_plural': 'Plans',
            },
        ),
        migrations.CreateModel(
            name='PlanPricing',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('price', models.DecimalField(max_digits=7, decimal_places=2, db_index=True)),
                ('plan', models.ForeignKey(to='plans.Plan')),
            ],
            options={
                'ordering': ('pricing__period',),
                'verbose_name': 'Plan pricing',
                'verbose_name_plural': 'Plans pricings',
            },
        ),
        migrations.CreateModel(
            name='PlanQuota',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('value', models.IntegerField(default=1, null=True, blank=True)),
                ('plan', models.ForeignKey(to='plans.Plan')),
            ],
            options={
                'verbose_name': 'Plan quota',
                'verbose_name_plural': 'Plans quotas',
            },
        ),
        migrations.CreateModel(
            name='Pricing',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100, verbose_name='name')),
                ('period', models.PositiveIntegerField(default=30, null=True, verbose_name='period', db_index=True, blank=True)),
                ('url', models.CharField(help_text='Optional link to page with more information (for clickable pricing table headers)', max_length=200, blank=True)),
            ],
            options={
                'ordering': ('period',),
                'verbose_name': 'Pricing',
                'verbose_name_plural': 'Pricings',
            },
        ),
        migrations.CreateModel(
            name='Quota',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.PositiveIntegerField(editable=False, db_index=True)),
                ('codename', models.CharField(unique=True, max_length=50, verbose_name='codename', db_index=True)),
                ('name', models.CharField(max_length=100, verbose_name='name')),
                ('unit', models.CharField(max_length=100, verbose_name='unit', blank=True)),
                ('description', models.TextField(verbose_name='description', blank=True)),
                ('is_boolean', models.BooleanField(default=False, verbose_name='is boolean')),
                ('url', models.CharField(help_text='Optional link to page with more information (for clickable pricing table headers)', max_length=200, blank=True)),
            ],
            options={
                'ordering': ('order',),
                'verbose_name': 'Quota',
                'verbose_name_plural': 'Quotas',
            },
        ),
        migrations.CreateModel(
            name='UserPlan',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('expire', models.DateField(default=None, null=True, verbose_name='expire', db_index=True, blank=True)),
                ('active', models.BooleanField(default=True, db_index=True, verbose_name='active')),
                ('plan', models.ForeignKey(verbose_name='plan', to='plans.Plan')),
                ('user', models.OneToOneField(verbose_name='user', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'User plan',
                'verbose_name_plural': 'Users plans',
            },
        ),
        migrations.AddField(
            model_name='planquota',
            name='quota',
            field=models.ForeignKey(to='plans.Quota'),
        ),
        migrations.AddField(
            model_name='planpricing',
            name='pricing',
            field=models.ForeignKey(to='plans.Pricing'),
        ),
        migrations.AddField(
            model_name='plan',
            name='quotas',
            field=models.ManyToManyField(to='plans.Quota', verbose_name='quotas', through='plans.PlanQuota'),
        ),
        migrations.AddField(
            model_name='order',
            name='plan',
            field=models.ForeignKey(related_name='plan_order', verbose_name='plan', to='plans.Plan'),
        ),
        migrations.AddField(
            model_name='order',
            name='pricing',
            field=models.ForeignKey(verbose_name='pricing', blank=True, to='plans.Pricing', null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='user',
            field=models.ForeignKey(verbose_name='user', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='invoice',
            name='order',
            field=models.ForeignKey(to='plans.Order'),
        ),
        migrations.AddField(
            model_name='invoice',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
    ]
