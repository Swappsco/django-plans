from decimal import Decimal
from datetime import date, datetime
from datetime import timedelta
import vatnumber

from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.core.urlresolvers import reverse
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core import mail
from django.db.models import Q
from django.utils import six
from django.utils.translation import get_language, activate


if six.PY2: # pragma: no cover
    import mock
elif six.PY3: # pragma: no cover
    from unittest import mock

from plans.models import PlanPricing, Invoice, Order, Plan, UserPlan, BillingInfo
from plans.plan_change import PlanChangePolicy, StandardPlanChangePolicy
from plans.taxation import TaxationPolicy
from plans.taxation.eu import EUTaxationPolicy
from plans.quota import get_user_quota
from plans.validators import ModelCountValidator
from plans.importer import import_name
from plans.admin import UserLinkMixin
from plans.contrib import send_template_email
from plans.forms import BillingInfoForm

from decimal import Decimal
User = get_user_model()


class PlansTestCase(TestCase):
    fixtures = ['initial_test_data', 'initial_plan', 'test_django-plans_auth', 'test_django-plans_plans']

    def setUp(self):
        mail.outbox = []

    def test_get_user_quota(self):
        u = User.objects.get(username='test1')
        self.assertEqual(get_user_quota(u),
                         {u'CUSTOM_WATERMARK': 1, u'MAX_GALLERIES_COUNT': 3, u'MAX_PHOTOS_PER_GALLERY': None})

    def test_get_plan_quota(self):
        u = User.objects.get(username='test1')
        p = u.userplan.plan
        self.assertEqual(p.get_quota_dict(),
                         {u'CUSTOM_WATERMARK': 1, u'MAX_GALLERIES_COUNT': 3, u'MAX_PHOTOS_PER_GALLERY': None})

    def test_save_adds_time_now_to_created(self):
        """
        If created is not setted, it should be assigned now()
        """
        plan = Plan.objects.create(name='my_plan')
        self.assertIsNotNone(plan.created)
        self.assertEqual(type(plan.created), type(datetime.now()))


    def test_extend_account_same_plan_future(self):
        u = User.objects.get(username='test1')
        u.userplan.expire = date.today() + timedelta(days=50)
        u.userplan.active = False
        u.userplan.save()
        plan_pricing = PlanPricing.objects.get(plan=u.userplan.plan, pricing__period=30)
        u.userplan.extend_account(plan_pricing.plan, plan_pricing.pricing)
        self.assertEqual(u.userplan.expire,
                         date.today() + timedelta(days=50) + timedelta(days=plan_pricing.pricing.period))
        self.assertEqual(u.userplan.plan, plan_pricing.plan)
        self.assertEqual(u.userplan.active, True)
        self.assertEqual(len(mail.outbox), 1)

    def test_extend_account_same_plan_before(self):
        u = User.objects.get(username='test1')
        u.userplan.expire = date.today() - timedelta(days=50)
        u.userplan.active = False
        u.userplan.save()
        plan_pricing = PlanPricing.objects.get(plan=u.userplan.plan, pricing__period=30)
        u.userplan.extend_account(plan_pricing.plan, plan_pricing.pricing)
        self.assertEqual(u.userplan.expire, date.today() + timedelta(days=plan_pricing.pricing.period))
        self.assertEqual(u.userplan.plan, plan_pricing.plan)
        self.assertEqual(u.userplan.active, True)
        self.assertEqual(len(mail.outbox), 1)

    def test_extend_account_other(self):
        """
        Tests extending account with other Plan that user had before:
        Tests if expire date is set correctly
        Tests if mail has been send
        Tests if account has been activated
        """
        u = User.objects.get(username='test1')
        u.userplan.expire = date.today() - timedelta(days=50)
        u.userplan.active = False
        u.userplan.save()
        plan_pricing = PlanPricing.objects.filter(~Q(plan=u.userplan.plan) & Q(pricing__period=30))[0]
        u.userplan.extend_account(plan_pricing.plan, plan_pricing.pricing)
        self.assertEqual(u.userplan.expire, date.today() + timedelta(days=plan_pricing.pricing.period))
        self.assertEqual(u.userplan.plan, plan_pricing.plan)
        self.assertEqual(u.userplan.active, True)
        self.assertEqual(len(mail.outbox), 1)

    def test_expire_account(self):
        u = User.objects.get(username='test1')
        u.userplan.expire = date.today() + timedelta(days=50)
        u.userplan.active = True
        u.userplan.save()
        u.userplan.expire_account()
        self.assertEqual(u.userplan.active, False)
        self.assertEqual(len(mail.outbox), 1)

    def test_remind_expire(self):
        u = User.objects.get(username='test1')
        u.userplan.expire = date.today() + timedelta(days=14)
        u.userplan.active = True
        u.userplan.save()
        u.userplan.remind_expire_soon()
        self.assertEqual(u.userplan.active, True)
        self.assertEqual(len(mail.outbox), 1)

    def test_disable_emails(self):
        with self.settings(SEND_PLANS_EMAILS=False):
            # Re-run the remind_expire test, but look for 0 emails sent
            u = User.objects.get(username='test1')
            u.userplan.expire = date.today() + timedelta(days=14)
            u.userplan.active = True
            u.userplan.save()
            u.userplan.remind_expire_soon()
            self.assertEqual(u.userplan.active, True)
            self.assertEqual(len(mail.outbox), 0)

    def test_switch_to_free_no_expiry(self):
        """
        Tests switching to a free Plan and checks that their expiry is cleared
        Tests if expire date is set correctly
        Tests if mail has been send
        Tests if account has been activated
        """
        u = User.objects.get(username='test1')
        self.assertIsNotNone(u.userplan.expire)

        plan = Plan.objects.get(name="Free")
        self.assertTrue(plan.is_free())
        self.assertNotEqual(u.userplan.plan, plan)

        # Switch to Free Plan
        u.userplan.extend_account(plan, None)
        self.assertEquals(u.userplan.plan, plan)
        self.assertIsNone(u.userplan.expire)
        self.assertEqual(u.userplan.active, True)


class UserPlanTestcase(TestCase):
    fixtures = ['initial_test_data', 'initial_plan', 'test_django-plans_auth', 'test_django-plans_plans']
    def setUp(self):
        self.userplan = User.objects.first().userplan # User plan which already expired

    def test_userplan_is_active_returns_active(self):
        """
        is_active should return userplan.active
        """
        
        self.assertFalse(self.userplan.active)
        self.userplan.active = True
        self.assertTrue(self.userplan.is_active())

    def test_is_expired_returns_none_if_expire_is_none(self):
        """
        None represents plans with no limit, so it always return
        false because it nevers expires
        """
        self.userplan.expire = None
        self.assertFalse(self.userplan.is_expired())

    def test_is_expired_returns_false_if_not_expired(self):
        """
        If there are still some days active, is_expired()
        should return None
        """
        delta = 3
        self.userplan.expire = datetime.now().date() + timedelta(days=delta)
        self.assertFalse(self.userplan.is_expired())

    def test_is_expired_returns_true_if_expired(self):
        """
        If plan is not None and has already expired, 
        is_expired() should return True
        """
        delta = -3
        self.userplan.expire = datetime.now().date() + timedelta(days=delta)
        self.assertTrue(self.userplan.is_expired())

    def test_days_left_returns_none_if_no_expiration(self):
        """
        If expiration is none, days left should return None
        """
        self.userplan.expire = None
        self.assertIsNone(self.userplan.days_left())

    def test_days_left_returns_negative_value_expired(self):
        """
        If plan expired already, days_left() should return
        a negative number representing the number of days since that
        """
        self.assertTrue(self.userplan.days_left()<0)

    def test_days_left_returns_positive_not_expired_yet(self):
        """
        If plan has not expired yet, days_left should return 
        a positive number of days representing the number of days
        left until the expiration
        """
        delta = 3
        self.userplan.expire = datetime.now().date() + timedelta(days=delta)
        self.assertEquals(delta, self.userplan.days_left())



class TestInvoice(TestCase):
    fixtures = ['initial_plan', 'test_django-plans_auth', 'test_django-plans_plans']

    def test_get_full_number(self):
        i = Invoice()
        i.number = 123
        i.issued = date(2010, 5, 30)
        self.assertEqual(i.get_full_number(), "123/FV/05/2010")

    def test_get_full_number_type1(self):
        i = Invoice()
        i.type = Invoice.INVOICE_TYPES.INVOICE
        i.number = 123
        i.issued = date(2010, 5, 30)
        self.assertEqual(i.get_full_number(), "123/FV/05/2010")

    def test_get_full_number_type2(self):
        i = Invoice()
        i.type = Invoice.INVOICE_TYPES.DUPLICATE
        i.number = 123
        i.issued = date(2010, 5, 30)
        self.assertEqual(i.get_full_number(), "123/FV/05/2010")

    def test_get_full_number_type3(self):
        i = Invoice()
        i.type = Invoice.INVOICE_TYPES.PROFORMA
        i.number = 123
        i.issued = date(2010, 5, 30)
        self.assertEqual(i.get_full_number(), "123/PF/05/2010")

    def test_get_full_number_with_settings(self):
        settings.PLANS_INVOICE_NUMBER_FORMAT = "{{ invoice.issued|date:'Y' }}." \
                                         "{{ invoice.number }}.{{ invoice.issued|date:'m' }}"
        i = Invoice()
        i.number = 123
        i.issued = date(2010, 5, 30)
        self.assertEqual(i.get_full_number(), "2010.123.05")

    def test_set_issuer_invoice_data_raise(self):
        issdata = settings.PLANS_INVOICE_ISSUER
        del settings.PLANS_INVOICE_ISSUER
        i = Invoice()
        self.assertRaises(ImproperlyConfigured, i.set_issuer_invoice_data)
        settings.PLANS_INVOICE_ISSUER = issdata

    def test_set_issuer_invoice_data(self):
        i = Invoice()
        i.set_issuer_invoice_data()
        self.assertEqual(i.issuer_name, settings.PLANS_INVOICE_ISSUER['issuer_name'])
        self.assertEqual(i.issuer_street, settings.PLANS_INVOICE_ISSUER['issuer_street'])
        self.assertEqual(i.issuer_zipcode, settings.PLANS_INVOICE_ISSUER['issuer_zipcode'])
        self.assertEqual(i.issuer_city, settings.PLANS_INVOICE_ISSUER['issuer_city'])
        self.assertEqual(i.issuer_country, settings.PLANS_INVOICE_ISSUER['issuer_country'])
        self.assertEqual(i.issuer_tax_number, settings.PLANS_INVOICE_ISSUER['issuer_tax_number'])

    # def test_set_buyer_invoice_data(self):
    #     i = Invoice()
    #     u = User.objects.get(username='test1')
    #     i.set_buyer_invoice_data(u.billinginfo)
    #     self.assertEqual(i.buyer_name, u.billinginfo.name)
    #     self.assertEqual(i.buyer_street, u.billinginfo.street)
    #     self.assertEqual(i.buyer_zipcode, u.billinginfo.zipcode)
    #     self.assertEqual(i.buyer_city, u.billinginfo.city)
    #     self.assertEqual(i.buyer_country, u.billinginfo.country)
    #     self.assertEqual(i.buyer_tax_number, u.billinginfo.tax_number)
    #     self.assertEqual(i.buyer_name, u.billinginfo.shipping_name)
    #     self.assertEqual(i.buyer_street, u.billinginfo.shipping_street)
    #     self.assertEqual(i.buyer_zipcode, u.billinginfo.shipping_zipcode)
    #     self.assertEqual(i.buyer_city, u.billinginfo.shipping_city)
    #     self.assertEqual(i.buyer_country, u.billinginfo.shipping_country)

    def test_invoice_number(self):
        settings.PLANS_INVOICE_NUMBER_FORMAT = "{{ invoice.number }}/{% ifequal " \
                                         "invoice.type invoice.INVOICE_TYPES.PROFORMA %}PF{% else %}FV" \
                                         "{% endifequal %}/{{ invoice.issued|date:'m/Y' }}"
        o = Order.objects.all()[0]
        day = date(2010, 5, 3)
        i = Invoice(issued=day, selling_date=day, payment_date=day)
        i.copy_from_order(o)
        i.set_issuer_invoice_data()
        i.set_buyer_invoice_data(o.user.billinginfo)
        i.clean()
        i.save()

        self.assertEqual(i.number, 1)
        self.assertEqual(i.full_number, '1/FV/05/2010')

    def test_invoice_number_daily(self):
        settings.PLANS_INVOICE_NUMBER_FORMAT = "{{ invoice.number }}/{% ifequal " \
                                         "invoice.type invoice.INVOICE_TYPES.PROFORMA %}PF{% else %}FV" \
                                         "{% endifequal %}/{{ invoice.issued|date:'d/m/Y' }}"
        settings.PLANS_INVOICE_COUNTER_RESET = Invoice.NUMBERING.DAILY

        user = User.objects.get(username='test1')
        plan_pricing = PlanPricing.objects.all()[0]
        tax = getattr(settings, "PLANS_TAX")
        currency = getattr(settings, "PLANS_CURRENCY")
        o1 = Order(user=user, plan=plan_pricing.plan,
                   pricing=plan_pricing.pricing, amount=plan_pricing.price,
                   tax=tax, currency=currency)
        o1.save()

        o2 = Order(user=user, plan=plan_pricing.plan,
                   pricing=plan_pricing.pricing, amount=plan_pricing.price,
                   tax=tax, currency=currency)
        o2.save()

        o3 = Order(user=user, plan=plan_pricing.plan,
                   pricing=plan_pricing.pricing, amount=plan_pricing.price,
                   tax=tax, currency=currency)
        o3.save()

        day = date(2001, 5, 3)
        i1 = Invoice(issued=day, selling_date=day, payment_date=day)
        i1.copy_from_order(o1)
        i1.set_issuer_invoice_data()
        i1.set_buyer_invoice_data(o1.user.billinginfo)
        i1.clean()
        i1.save()

        i2 = Invoice(issued=day, selling_date=day, payment_date=day)
        i2.copy_from_order(o2)
        i2.set_issuer_invoice_data()
        i2.set_buyer_invoice_data(o2.user.billinginfo)
        i2.clean()
        i2.save()

        day = date(2001, 5, 4)
        i3 = Invoice(issued=day, selling_date=day, payment_date=day)
        i3.copy_from_order(o1)
        i3.set_issuer_invoice_data()
        i3.set_buyer_invoice_data(o1.user.billinginfo)
        i3.clean()
        i3.save()

        self.assertEqual(i1.full_number, "1/FV/03/05/2001")
        self.assertEqual(i2.full_number, "2/FV/03/05/2001")
        self.assertEqual(i3.full_number, "1/FV/04/05/2001")

    def test_invoice_number_monthly(self):
        settings.PLANS_INVOICE_NUMBER_FORMAT = "{{ invoice.number }}/{% ifequal " \
                                         "invoice.type invoice.INVOICE_TYPES.PROFORMA %}PF{% else %}FV" \
                                         "{% endifequal %}/{{ invoice.issued|date:'m/Y' }}"
        settings.PLANS_INVOICE_COUNTER_RESET = Invoice.NUMBERING.MONTHLY

        user = User.objects.get(username='test1')
        plan_pricing = PlanPricing.objects.all()[0]
        tax = getattr(settings, "PLANS_TAX")
        currency = getattr(settings, "PLANS_CURRENCY")
        o1 = Order(user=user, plan=plan_pricing.plan,
                   pricing=plan_pricing.pricing, amount=plan_pricing.price,
                   tax=tax, currency=currency)
        o1.save()

        o2 = Order(user=user, plan=plan_pricing.plan,
                   pricing=plan_pricing.pricing, amount=plan_pricing.price,
                   tax=tax, currency=currency)
        o2.save()

        o3 = Order(user=user, plan=plan_pricing.plan,
                   pricing=plan_pricing.pricing, amount=plan_pricing.price,
                   tax=tax, currency=currency)
        o3.save()

        day = date(2002, 5, 3)
        i1 = Invoice(issued=day, selling_date=day, payment_date=day)
        i1.copy_from_order(o1)
        i1.set_issuer_invoice_data()
        i1.set_buyer_invoice_data(o1.user.billinginfo)
        i1.clean()
        i1.save()

        day = date(2002, 5, 13)
        i2 = Invoice(issued=day, selling_date=day, payment_date=day)
        i2.copy_from_order(o2)
        i2.set_issuer_invoice_data()
        i2.set_buyer_invoice_data(o2.user.billinginfo)
        i2.clean()
        i2.save()

        day = date(2002, 6, 1)
        i3 = Invoice(issued=day, selling_date=day, payment_date=day)
        i3.copy_from_order(o1)
        i3.set_issuer_invoice_data()
        i3.set_buyer_invoice_data(o1.user.billinginfo)
        i3.clean()
        i3.save()

        self.assertEqual(i1.full_number, "1/FV/05/2002")
        self.assertEqual(i2.full_number, "2/FV/05/2002")
        self.assertEqual(i3.full_number, "1/FV/06/2002")

    def test_invoice_number_annually(self):
        settings.PLANS_INVOICE_NUMBER_FORMAT = "{{ invoice.number }}/{% ifequal " \
                                         "invoice.type invoice.INVOICE_TYPES.PROFORMA %}PF{% else %}FV" \
                                         "{% endifequal %}/{{ invoice.issued|date:'Y' }}"
        settings.PLANS_INVOICE_COUNTER_RESET = Invoice.NUMBERING.ANNUALLY

        user = User.objects.get(username='test1')
        plan_pricing = PlanPricing.objects.all()[0]
        tax = getattr(settings, "PLANS_TAX")
        currency = getattr(settings, "PLANS_CURRENCY")
        o1 = Order(user=user, plan=plan_pricing.plan,
                   pricing=plan_pricing.pricing, amount=plan_pricing.price,
                   tax=tax, currency=currency)
        o1.save()

        o2 = Order(user=user, plan=plan_pricing.plan,
                   pricing=plan_pricing.pricing, amount=plan_pricing.price,
                   tax=tax, currency=currency)
        o2.save()

        o3 = Order(user=user, plan=plan_pricing.plan,
                   pricing=plan_pricing.pricing, amount=plan_pricing.price,
                   tax=tax, currency=currency)
        o3.save()

        day = date(1991, 5, 3)
        i1 = Invoice(issued=day, selling_date=day, payment_date=day)
        i1.copy_from_order(o1)
        i1.set_issuer_invoice_data()
        i1.set_buyer_invoice_data(o1.user.billinginfo)
        i1.clean()
        i1.save()

        day = date(1991, 7, 13)
        i2 = Invoice(issued=day, selling_date=day, payment_date=day)
        i2.copy_from_order(o2)
        i2.set_issuer_invoice_data()
        i2.set_buyer_invoice_data(o2.user.billinginfo)
        i2.clean()
        i2.save()

        day = date(1992, 6, 1)
        i3 = Invoice(issued=day, selling_date=day, payment_date=day)
        i3.copy_from_order(o1)
        i3.set_issuer_invoice_data()
        i3.set_buyer_invoice_data(o1.user.billinginfo)
        i3.clean()
        i3.save()

        self.assertEqual(i1.full_number, "1/FV/1991")
        self.assertEqual(i2.full_number, "2/FV/1991")
        self.assertEqual(i3.full_number, "1/FV/1992")

    def test_set_order(self):
        o = Order.objects.all()[0]

        i = Invoice()
        i.copy_from_order(o)

        self.assertEqual(i.order, o)
        self.assertEqual(i.user, o.user)
        self.assertEqual(i.total_net, o.amount)
        self.assertEqual(i.unit_price_net, o.amount)
        self.assertEqual(i.total, o.total())
        self.assertEqual(i.tax, o.tax)
        self.assertEqual(i.tax_total, o.total() - o.amount)
        self.assertEqual(i.currency, o.currency)


class OrderTestCase(TestCase):
    def test_amount_taxed_none(self):
        o = Order()
        o.amount = Decimal(123)
        o.tax = None
        self.assertEqual(o.total(), Decimal('123'))

    def test_amount_taxed_0(self):
        o = Order()
        o.amount = Decimal(123)
        o.tax = Decimal(0)
        self.assertEqual(o.total(), Decimal('123'))

    def test_amount_taxed_23(self):
        o = Order()
        o.amount = Decimal(123)
        o.tax = Decimal(23)
        self.assertEqual(o.total(), Decimal('151.29'))


class PlanChangePolicyTestCase(TestCase):
    fixtures = ['initial_plan', 'test_django-plans_auth', 'test_django-plans_plans']

    def setUp(self):
        self.policy = PlanChangePolicy()

    def test_calculate_day_cost(self):
        plan = Plan.objects.get(pk=5)
        self.assertEqual(self.policy._calculate_day_cost(plan, 13), Decimal('6.67'))

    def test_get_change_price(self):
        p1 = Plan.objects.get(pk=3)
        p2 = Plan.objects.get(pk=4)
        self.assertEqual(self.policy.get_change_price(p1, p2, 23), Decimal('7.82'))
        self.assertEqual(self.policy.get_change_price(p2, p1, 23), None)

    def test_get_change_price1(self):
        p1 = Plan.objects.get(pk=3)
        p2 = Plan.objects.get(pk=4)
        self.assertEqual(self.policy.get_change_price(p1, p2, 53), Decimal('18.02'))
        self.assertEqual(self.policy.get_change_price(p2, p1, 53), None)

    def test_get_change_price2(self):
        p1 = Plan.objects.get(pk=3)
        p2 = Plan.objects.get(pk=4)
        self.assertEqual(self.policy.get_change_price(p1, p2, -53), None)
        self.assertEqual(self.policy.get_change_price(p1, p2, 0), None)


class StandardPlanChangePolicyTestCase(TestCase):
    fixtures = ['initial_plan', 'test_django-plans_auth', 'test_django-plans_plans']

    def setUp(self):
        self.policy = StandardPlanChangePolicy()

    def test_get_change_price(self):
        p1 = Plan.objects.get(pk=3)
        p2 = Plan.objects.get(pk=4)
        self.assertEqual(self.policy.get_change_price(p1, p2, 23), Decimal('8.60'))
        self.assertEqual(self.policy.get_change_price(p2, p1, 23), None)

class TaxationPolicyTestCase(TestCase):

    def setUp(self):
        self.taxation_policy = TaxationPolicy()

    def test_taxation_policy_returns_plans_tax_or_none(self):
        """
        PLANS_TAX should be returned if it exists, otherwise None should
        be returned
        """
        tax_value = Decimal(15.0)
        with self.settings(PLANS_TAX=tax_value):
            self.assertEquals(tax_value, self.taxation_policy.get_default_tax())
        with self.settings(PLANS_TAX=None):
            self.assertEquals(None, self.taxation_policy.get_default_tax())

    def test_taxation_policy_raise_error_default_is_not_decimal(self):
        """
        If PLANS_TAX is not a decimal or None, then a ValueError should be
        raised by the application.
        """
        with self.settings(PLANS_TAX=''):
            self.assertRaises(TypeError, self.taxation_policy.get_default_tax)

    def test_get_tax_rate_raises_not_implemented(self):
        """
        This method should be overriden by children. Should raise
        NotImplementedError exception by default
        """
        with self.assertRaises(NotImplementedError):
            self.taxation_policy.get_tax_rate('tax_id', 'country_code')
                


class EUTaxationPolicyTestCase(TestCase):
    def setUp(self):
        self.policy = EUTaxationPolicy()

    def test_none(self):
        with self.settings(PLANS_TAX=Decimal('23.0'), PLANS_TAX_COUNTRY='PL'):
            self.assertEqual(self.policy.get_tax_rate(None, None), Decimal('23.0'))

    def test_private_nonEU(self):
        with self.settings(PLANS_TAX=Decimal('23.0'), PLANS_TAX_COUNTRY='PL'):
            self.assertEqual(self.policy.get_tax_rate(None, 'RU'), None)

    def test_private_EU_same(self):
        with self.settings(PLANS_TAX=Decimal('23.0'), PLANS_TAX_COUNTRY='PL'):
            self.assertEqual(self.policy.get_tax_rate(None, 'PL'), Decimal('23.0'))

    def test_private_EU_notsame(self):
        with self.settings(PLANS_TAX=Decimal('23.0'), PLANS_TAX_COUNTRY='PL'):
            self.assertEqual(self.policy.get_tax_rate(None, 'AT'), Decimal('20.0'))

    def test_company_nonEU(self):
        with self.settings(PLANS_TAX=Decimal('23.0'), PLANS_TAX_COUNTRY='PL'):
            self.assertEqual(self.policy.get_tax_rate('123456', 'RU'), None)

    def test_company_EU_same(self):
        with self.settings(PLANS_TAX=Decimal('23.0'), PLANS_TAX_COUNTRY='PL'):
            self.assertEqual(self.policy.get_tax_rate('123456', 'PL'), Decimal('23.0'))

    @mock.patch("vatnumber.check_vies", lambda x: True)
    def test_company_EU_notsame_vies_ok(self):
        with self.settings(PLANS_TAX=Decimal('23.0'), PLANS_TAX_COUNTRY='PL'):
            self.assertEqual(self.policy.get_tax_rate('123456', 'AT'), None)

    @mock.patch("vatnumber.check_vies", lambda x: False)
    def test_company_EU_notsame_vies_not_ok(self):
        with self.settings(PLANS_TAX=Decimal('23.0'), PLANS_TAX_COUNTRY='PL'):
            self.assertEqual(self.policy.get_tax_rate('123456', 'AT'), Decimal('20.0'))


class ValidatorsTestCase(TestCase):
    fixtures = ['initial_plan', 'test_django-plans_auth', 'test_django-plans_plans']
    def test_model_count_validator(self):
        """
        We create a test model validator for User. It will raise ValidationError when QUOTA_NAME value
        will be lower than number of elements of model User.
        """

        class TestValidator(ModelCountValidator):
            code = 'QUOTA_NAME'
            model = User

        validator_object = TestValidator()
        self.assertRaises(ValidationError, validator_object, user=None, quota_dict={'QUOTA_NAME': 1})
        self.assertEqual(validator_object(user=None, quota_dict={'QUOTA_NAME': 2}), None)
        self.assertEqual(validator_object(user=None, quota_dict={'QUOTA_NAME': 3}), None)


        #   TODO: FIX this test not to use Pricing for testing  ModelAttributeValidator
        # def test_model_attribute_validator(self):
        #     """
        #     We create a test attribute validator which will validate if Pricing objects has a specific value set.
        #     """
        #
        #     class TestValidator(ModelAttributeValidator):
        #         code = 'QUOTA_NAME'
        #         attribute = 'period'
        #         model = Pricing
        #
        #     validator_object = TestValidator()
        #     self.assertRaises(ValidationError, validator_object, user=None, quota_dict={'QUOTA_NAME': 360})
        #     self.assertEqual(validator_object(user=None, quota_dict={'QUOTA_NAME': 365}), None)

class ImporterTestCase(TestCase):

    def setUp(self):
        pass

    def test_import_name_imports_module_by_path(self):
        """
        import_name should be able to import a module with
        its python path
        """
        module_name = 'abc.ABCMeta'
        self.assertEqual(type(import_name(module_name)), type(TypeError))

class ContribTestCase(TestCase):

    def setUp(self):
        pass

    def test_send_template_email_does_not_modify_language(self):
        """
        Language is changed inside the method, but should be restored
        before returning or that may cause unintended side effects
        """
        activate('pt_BR')
        test_lang = get_language()
        send_template_email(['test@test.com'], 'mail/change_plan_title.txt',
            'mail/change_plan_body.txt', {}, 'en-us')
        self.assertEqual(test_lang, get_language())

class FormsTestCase(TestCase):
    fixtures = ['initial_plan', 'test_django-plans_auth', 'test_django-plans_plans']
    def setUp(self):
        pass

    def test_form_clean_raises_error_on_invalid_tax(self):
        """
        BillingInfo form should allow only valid tax numbers.
        Form should return the error if it is not
        """
        billing_info = BillingInfo.objects.first()
        country = vatnumber.countries()[0]
        data = {
            'user': billing_info.user,
            'country': country,
            'street': billing_info.street,
            'name': billing_info.name,
            'zipcode': billing_info.zipcode,
            'city': billing_info.city,
            'tax_number': country+billing_info.tax_number,
        }
        form = BillingInfoForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 1)
        
class ViewsTestCase(TestCase):
    fixtures = ['initial_plan', 'test_django-plans_auth', 'test_django-plans_plans']
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_superuser(
            username='test', email='test@test.com', password='top_secret')
        self.client.login(username=self.user.username, password='top_secret')
        
    def test_invoice_returns_html_if_not_wkhtmltopdf(self):
        """
        If wkhtmltopf is not installed, the invoice detail view
        should return the invoice as html
        """
        response = self.client.get(reverse('invoice_preview', 
            args=[Invoice.objects.first().pk]))
        self.assertTrue(b'Content-Type: text/html' in response.serialize_headers())
        self.assertEqual(response.status_code, 200)
        
    
    