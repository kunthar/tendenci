from django.core.urlresolvers import reverse
from django.db import models
from django.utils.translation import ugettext, ugettext_lazy as _
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic

from tendenci.apps.forms_builder.forms.settings import FIELD_MAX_LENGTH, LABEL_MAX_LENGTH
from tendenci.apps.forms_builder.forms.managers import FormManager
from tendenci.core.perms.models import TendenciBaseModel
from tendenci.core.perms.object_perms import ObjectPermission
from tendenci.apps.user_groups.models import Group, GroupMembership
from tendenci.core.site_settings.utils import get_setting

#STATUS_DRAFT = 1
#STATUS_PUBLISHED = 2
STATUS_CHOICES = (
    ('draft', "Draft"),
    ('published', "Published"),
)

FIELD_CHOICES = (
    ("CharField", _("Text")),
    ("CharField/django.forms.Textarea", _("Paragraph Text")),
    ("BooleanField", _("Checkbox")),
    ("ChoiceField", _("Choose from a list")),
    ("MultipleChoiceField/django.forms.CheckboxSelectMultiple", _("Multi-select - Checkboxes")),
    ("MultipleChoiceField", _("Multi-select - Select Many")),
    ("EmailVerificationField", _("Email")),
    ("FileField", _("File upload")),
    ("DateField/django.forms.extras.SelectDateWidget", _("Date - Select")),
    ("DateField/django.forms.DateInput", _("Date - Text Input")),
    ("DateTimeField", _("Date/time")),
    ("CharField/tendenci.apps.forms_builder.forms.widgets.Description", _("Description")),
    ("CharField/tendenci.apps.forms_builder.forms.widgets.Header", _("Section Heading")),
)

FIELD_FUNCTIONS = (
    ("group_subscription", _("Subscribe to Group")),
    ("first_name", _("First Name")),
    ("last_name", _("Last Name")),
    ("email", _("Email")),

    ("address", _("Address")),
    ("city", _("City")),
    ("state", _("State")),
    ("zip_code", _("Zip Code")),
    ("country", _("Country")),
    ("phone", _("Phone")),
    ("position_title", _("Position Title")),
    ("comments", _("Comments")),

    ("company_name", _("Company Name")),
    ("company_address", _("Company Address")),
    ("company_city", _("Company City")),
    ("company_state", _("Company State")),
    ("company_zip_code", _("Company Zip Code")),
    ("company_country", _("Company Country")),
    ("company_phone", _("Company Phone")),
)

BILLING_PERIOD_CHOICES = (
    ('month', _('Month(s)')),
    ('year', _('Year(s)')),
    ('week', _('Week(s)')),
    ('day', _('Day(s)')),
)

DUE_SORE_CHOICES = (
    ('start', _('start')),
    ('end', _('end')),
)


class Form(TendenciBaseModel):
    """
    A user-built form.
    """

    title = models.CharField(_("Title"), max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    intro = models.TextField(_("Intro"), max_length=2000, blank=True)
    response = models.TextField(_("Confirmation Text"), max_length=2000, blank=True)
    email_text = models.TextField(_("Email Text to Submitter"), default='', blank=True,
        help_text=_("If Send email is checked, this is the text that will be sent in an email to the person submitting the form."), max_length=2000)
    subject_template = models.CharField(_("Template for email subject "),
        help_text=_("""Options include [title] for form title, and
                        name of form fields inside brackets [ ]. E.x. [first name] or
                        [email address]"""),
        default="[title] - [first name]  [last name] - [phone]",
        max_length=200,
        blank=True, null=True)
    send_email = models.BooleanField(_("Send email"), default=False,
        help_text=_("If checked, the person submitting the form will be sent an email."))
    email_from = models.EmailField(_("Reply-To address"), blank=True,
        help_text=_("The address the replies to the email will be sent to"))
    email_copies = models.CharField(_("Send copies to"), blank=True,
        help_text=_("One or more email addresses, separated by commas"),
        max_length=2000)
    completion_url = models.URLField(_("Completion URL"), blank=True, null=True,
        help_text=_("Redirect to this page after form completion."))
    template = models.CharField(_('Template'), max_length=50, blank=True)

    # payments
    custom_payment = models.BooleanField(_("Is Custom Payment"), default=False,
        help_text=_("If checked, please add pricing options below. Leave the price blank if users can enter their own amount."))
    recurring_payment = models.BooleanField(_("Is Recurring Payment"), default=False,
        help_text=_("If checked, please add pricing options below. Leave the price blank if users can enter their own amount."))
    payment_methods = models.ManyToManyField("payments.PaymentMethod", blank=True)

    # popular fields
    first_name = models.BooleanField(_('First Name'), default=False)
    last_name = models.BooleanField(_('Last Name'), default=False)
    email = models.BooleanField(_('Email'), default=False)
    position_title = models.BooleanField(_('Position Title'), default=False)
    url = models.BooleanField(_('URL'), default=False)
    comments = models.BooleanField(_('Comments'), default=False)

    address = models.BooleanField(_('Address'), default=False)
    city = models.BooleanField(_('City'), default=False)
    state = models.BooleanField(_('State'), default=False)
    zipcode = models.BooleanField(_('Zip Code'), default=False)
    country = models.BooleanField(_('Country'), default=False)
    phone = models.BooleanField(_('Phone'), default=False)

    company_name = models.BooleanField(_('Company Name'), default=False)
    company_address = models.BooleanField(_('Company Address'), default=False)
    company_city = models.BooleanField(_('Company City'), default=False)
    company_state = models.BooleanField(_('Company State'), default=False)
    company_zipcode = models.BooleanField(_('Company Zip Code'), default=False)
    company_country = models.BooleanField(_('Company Country'), default=False)
    company_phone = models.BooleanField(_('Company Phone'), default=False)

    perms = generic.GenericRelation(ObjectPermission,
        object_id_field="object_id", content_type_field="content_type")

    objects = FormManager()

    class Meta:
        verbose_name = _("Form")
        verbose_name_plural = _("Forms")
        permissions = (("view_form", "Can view form"),)

    def __unicode__(self):
        return self.title

    @models.permalink
    def get_absolute_url(self):
        return ("form_detail", (), {"slug": self.slug})

    def get_payment_type(self):
        if self.recurring_payment and self.custom_payment:
            return "Custom Recurring Payment"
        if self.recurring_payment:
            return "Recurring Payment"
        if self.custom_payment:
            return "Custom Payment"

    def admin_link_view(self):
        url = self.get_absolute_url()
        return "<a href='%s'>%s</a>" % (url, ugettext("View on site"))
    admin_link_view.allow_tags = True
    admin_link_view.short_description = ""

    def admin_link_export(self):
        url = reverse("admin:forms_form_export", args=(self.id,))
        return "<a href='%s'>%s</a>" % (url, ugettext("Export entries"))
    admin_link_export.allow_tags = True
    admin_link_export.short_description = ""

    def has_files(self):
        for entry in self.entries.all():
            for field in entry.fields.all():
                if field.field.field_type == 'FileField':
                    return True
        return False


class FieldManager(models.Manager):
    """
    Only show visible fields when displaying actual form..
    """
    def visible(self):
        return self.filter(visible=True)


class Field(models.Model):
    """
    A field for a user-built form.
    'field_function' has the following options:
    "GroupSubscription"
    - Subscribes form entries to the group specified
    - Required to be a BooleanField
    "first_name", "last_name", "phone_number"
    - Markers for specific fields that need to be referenced in emails
    - Required to be a CharField
    - Includes their respective values to the email's subject
    """

    form = models.ForeignKey("Form", related_name="fields")
    label = models.CharField(_("Label"), max_length=LABEL_MAX_LENGTH)
    field_function = models.CharField(_('Field Function'),
        choices=FIELD_FUNCTIONS, max_length=64, null=True, blank=True)
    field_type = models.CharField(_("Type"), choices=FIELD_CHOICES, max_length=64)
    function_params = models.CharField(_("Group Name(s)"),
        max_length=100, null=True, blank=True, help_text="Comma separated if more than one")
    required = models.BooleanField(_("Required"), default=True)
    visible = models.BooleanField(_("Visible"), default=True)
    choices = models.CharField(_("Choices"), max_length=1000, blank=True,
        help_text="Comma separated options where applicable")
    position = models.PositiveIntegerField(_('position'), default=0)
    default = models.CharField(_("Default"), max_length=1000, blank=True,
        help_text="Default value of the field")

    objects = FieldManager()

    class Meta:
        verbose_name = _("Field")
        verbose_name_plural = _("Fields")
        ordering = ('position',)

    def __unicode__(self):
        return self.label

    def get_field_class(self):
        if "/" in self.field_type:
            field_class, field_widget = self.field_type.split("/")
        else:
            field_class, field_widget = self.field_type, None
        return field_class

    def get_field_widget(self):
        if "/" in self.field_type:
            field_class, field_widget = self.field_type.split("/")
        else:
            field_class, field_widget = self.field_type, None
        return field_widget

    def execute_function(self, entry, value, user=None):
        if self.field_function == "group_subscription":
            if value:
                for val in self.function_params.split(','):
                    group = Group.objects.get(name=val)
                    if user:
                        try:
                            group_membership = GroupMembership.objects.get(group=group, member=user)
                        except GroupMembership.DoesNotExist:
                            group_membership = GroupMembership(group=group, member=user)
                            group_membership.creator_id = user.id
                            group_membership.creator_username = user.username
                            group_membership.role = 'subscriber'
                            group_membership.owner_id = user.id
                            group_membership.owner_username = user.username
                            group_membership.save()
                    else:
                        entry.subscribe(group)  # subscribe form-entry to a group


class FormEntry(models.Model):
    """
    An entry submitted via a user-built form.
    """

    form = models.ForeignKey("Form", related_name="entries")
    entry_time = models.DateTimeField(_("Date/time"))
    entry_path = models.CharField(max_length=200, blank=True, default="")
    payment_method = models.ForeignKey('payments.PaymentMethod', null=True)
    pricing = models.ForeignKey('Pricing', null=True)
    creator = models.ForeignKey(User, related_name="formentry_creator",  null=True, on_delete=models.SET_NULL)
    create_dt = models.DateTimeField(auto_now_add=True)
    update_dt = models.DateTimeField(auto_now=True)

    # popular field --------------------------------------------------------
    first_name = models.CharField(max_length=200, blank=True, editable=False)
    last_name = models.CharField(max_length=200, blank=True, editable=False)
    email = models.CharField(max_length=200, blank=True, editable=False)
    position_title = models.CharField(max_length=500, blank=True, editable=False)
    url = models.URLField(blank=True, editable=False)
    comments = models.TextField(blank=True, editable=False)

    address = models.CharField(max_length=100, blank=True, editable=False)
    city = models.CharField(max_length=100, blank=True, editable=False)
    state = models.CharField(max_length=100, blank=True, editable=False)
    zipcode = models.CharField(max_length=100, blank=True, editable=False)
    country = models.CharField(max_length=100, blank=True, editable=False)
    phone = models.CharField(max_length=50, blank=True, editable=False)

    company_name = models.CharField(max_length=500, blank=True, editable=False)
    company_address = models.CharField(max_length=100, blank=True, editable=False)
    company_city = models.CharField(max_length=100, blank=True, editable=False)
    company_state = models.CharField(max_length=100, blank=True, editable=False)
    company_zipcode = models.CharField(max_length=100, blank=True, editable=False)
    company_country = models.CharField(max_length=100, blank=True, editable=False)
    company_phone = models.CharField(max_length=50, blank=True, editable=False)

    class Meta:
        verbose_name = _("Form entry")
        verbose_name_plural = _("Form entries")

    def __unicode__(self):
        u = ''
        for f in self.fields.all()[0:5]:
            u = u + str(f) + ' '
        return u[0:len(u) - 1]

    @models.permalink
    def get_absolute_url(self):
        return ("form_entry_detail", (), {"id": self.pk})

    def subscribe(self, group):
        """
        Subscribe FormEntry to group specified.
        """
        # avoiding circular imports
        from tendenci.apps.subscribers.models import GroupSubscription as GS
        try:
            GS.objects.get(group=group, subscriber=self)
        except GS.DoesNotExist:
            GS.objects.create(group=group, subscriber=self)

    def unsubscribe(self, group):
        """
        Unsubscribe FormEntry from group specified
        """
        # avoiding circular imports
        from tendenci.apps.subscribers.models import GroupSubscription as GS
        try:
            sub = GS.objects.get(group=group, subscriber=self)
            sub.delete()
        except GS.DoesNotExist:
            pass

    def entry_fields(self):
        return self.fields.all().order_by('field__position')

    def get_name_email(self):
        """Try to figure out the name and email from this entry
            Assume: 1) email field type is EmailField
                    2) use the labels to identify the name.
            We might need a better solution because this will not work
            if the form is not in English, or labels for names are not
            'first name', 'last name' or 'name'.
            Update: You can now use the special functions that start with
            "Email" to mark fields you need for this method
            instead of relying on the label as a marker.
        """
        field_entries = self.fields.all()
        first_name = ""
        last_name = ""
        name = ""
        email = ""
        for entry in field_entries:
            field = entry.field
            if field.field_type.lower() == 'emailfield':
                email = entry.value
            if field.field_type.lower() == 'emailverificationfield':
                email = entry.value
            if field.label.lower() in ['name']:
                name = entry.value
            if field.label.lower() in ['first name']:
                first_name = entry.value
            if field.label.lower() in ['last name']:
                last_name = entry.value
        if not name:
            if first_name or last_name:
                name = '%s %s' % (first_name, last_name)
        if not name:
            # pick the name from email
            if email:
                if '@' in email:
                    name, domain = email.split('@')
                else:
                    name = email

        return (name, email)

    def get(self, field_function):
        """
        Returns the value of the a field entry based
        on the field_function specified
        """
        for entry in self.fields.all():
            if entry.field.field_function == field_function:
                return entry.value
        return u''

    def get_type_of(self, field_type):
        """
        Returns the value of the a field entry based
        on the field_type specified
        """
        for entry in self.fields.all():
            if entry.field.field_type.lower() == field_type:
                return entry.value
        return u''

    def get_first_name(self):
        return self.get("first_name")

    def get_last_name(self):
        return self.get("last_name")

    def get_full_name(self):
        return self.get("full_name")

    def get_phone_number(self):
        return self.get("phone")

    def get_email_address(self):
        return self.get_type_of("emailverificationfield")

     # Called by payments_pop_by_invoice_user in Payment model.
    def get_payment_description(self, inv):
        """
        The description will be sent to payment gateway and displayed on invoice.
        If not supplied, the default description will be generated.
        This will pass the First Name and Last Name from the "Billing Information" screen, the value in the "Site Display Name"
        setting in Site Settings, and the name of the form that was submitted.
        """
        description = '%s Invoice %d, form: "%s", Form Entry Id (%d), billed to: %s %s.' % (
            get_setting('site', 'global', 'sitedisplayname'),
            inv.id,
            self.form.title,
            inv.object_id,
            inv.bill_to_first_name,
            inv.bill_to_last_name,
        )

        return description


class FieldEntry(models.Model):
    """
    A single field value for a form entry submitted via a user-built form.
    """

    entry = models.ForeignKey("FormEntry", related_name="fields")
    field = models.ForeignKey("Field", related_name="field")
    value = models.CharField(max_length=FIELD_MAX_LENGTH)

    class Meta:
        verbose_name = _("Form field entry")
        verbose_name_plural = _("Form field entries")

    def __unicode__(self):
        return ('%s: %s' % (self.field.label, self.value))

    def include_in_email(self):
        widget = self.field.get_field_widget()
        field_class = self.field.get_field_class()
        if widget == 'tendenci.apps.forms_builder.forms.widgets.Description':
            return False
        if widget == 'tendenci.apps.forms_builder.forms.widgets.Header':
            return False
        if field_class == 'FileField':
            return False
        return True

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(FieldEntry, self).save(*args, **kwargs)
        self.field.execute_function(self.entry, self.value, user=user)


class Pricing(models.Model):
    """
    Pricing options for custom payment forms.
    """
    form = models.ForeignKey('Form')
    label = models.CharField(max_length=100)

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Leaving this field blank allows visitors to set their own price"
    )

    # Recurring payment fields
    taxable = models.BooleanField(default=False)
    tax_rate = models.DecimalField(blank=True, max_digits=5, decimal_places=4, default=0,
                                   help_text='Example: 0.0825 for 8.25%.')
    billing_period = models.CharField(max_length=50, choices=BILLING_PERIOD_CHOICES,
                                        default='month')
    billing_frequency = models.IntegerField(default=1)
    num_days = models.IntegerField(default=0)
    due_sore = models.CharField(_("Billing cycle start or end date"), max_length=20,
                                   choices=DUE_SORE_CHOICES, default='start')
    has_trial_period = models.BooleanField(default=False)
    trial_period_days = models.IntegerField(default=0)
    trial_amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True, default=0.0)

    def __unicode__(self):
        currency_symbol = get_setting("site", "global", "currencysymbol")
        if not currency_symbol:
            currency_symbol = '$'
        return "%s - %s%s" % (self.label, currency_symbol, self.price, )
