from django.test import TestCase
from django.contrib.auth import get_user_model
from customer.models import Customer, Package, Payment
from customer.tests import CustomerFactory, PackageFactory, PaymentFactory, UserFactory

User = get_user_model()


class CustomerModelTest(TestCase):
    def setUp(self):
        self.package = PackageFactory()
        self.user = UserFactory()
        self.customer = CustomerFactory(
            package=self.package,
            user=self.user,
            nid="1234567890"
        )

    def test_customer_creation_with_nid(self):
        """Test that customer can be created with NID field"""
        self.assertEqual(self.customer.nid, "1234567890")
        self.assertEqual(self.customer.name, self.customer.name)
        self.assertEqual(self.customer.phone, self.customer.phone)

    def test_customer_str_representation(self):
        """Test customer string representation"""
        expected = f"{self.customer.name} ({self.customer.phone})"
        self.assertEqual(str(self.customer), expected)

    def test_customer_nid_optional(self):
        """Test that NID field is optional"""
        customer_without_nid = CustomerFactory(nid="")
        self.assertEqual(customer_without_nid.nid, "")


class PaymentModelTest(TestCase):
    def setUp(self):
        self.collector = UserFactory()
        self.customer = CustomerFactory()
        self.payment = PaymentFactory(
            customer=self.customer,
            entry_by=self.collector
        )

    def test_payment_creation_with_collector(self):
        """Test that payment can be created with entry_by field"""
        self.assertEqual(self.payment.entry_by, self.collector)
        self.assertEqual(self.payment.customer, self.customer)

    def test_payment_str_representation(self):
        """Test payment string representation"""
        expected = f"Payment of ${self.payment.amount:.2f} by {self.customer.name} on {self.payment.payment_date}"
        self.assertEqual(str(self.payment), expected)

    def test_payment_entry_by_optional(self):
        """Test that entry_by field is optional"""
        payment_without_collector = PaymentFactory(entry_by=None)
        self.assertIsNone(payment_without_collector.entry_by)


class CustomerFactoryTest(TestCase):
    def test_customer_factory_creates_nid(self):
        """Test that CustomerFactory generates NID"""
        customer = CustomerFactory()
        self.assertIsNotNone(customer.nid)
        self.assertTrue(len(customer.nid) > 0)

    def test_customer_factory_unique_nid(self):
        """Test that CustomerFactory generates unique NIDs"""
        customer1 = CustomerFactory()
        customer2 = CustomerFactory()
        self.assertNotEqual(customer1.nid, customer2.nid)


class PaymentFactoryTest(TestCase):
    def test_payment_factory_creates_entry_by(self):
        """Test that PaymentFactory generates entry_by"""
        payment = PaymentFactory()
        self.assertIsNotNone(payment.entry_by)
        self.assertIsInstance(payment.entry_by, User) 