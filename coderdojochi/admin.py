# -*- coding: utf-8 -*-
from datetime import datetime

from django.contrib import admin
from django.contrib.auth import get_user_model
# from django.core.urlresolvers import reverse
from django.db.models import Count
# from django.template.defaultfilters import pluralize
# from django.utils.safestring import mark_safe

from import_export import resources
from import_export.admin import (
    ImportExportActionModelAdmin,
    ImportExportMixin,
)

from import_export.fields import Field

from coderdojochi.models import (
    Course,
    Donation,
    Equipment,
    EquipmentType,
    Guardian,
    Location,
    Meeting,
    MeetingOrder,
    MeetingType,
    Mentor,
    MentorOrder,
    Order,
    RaceEthnicity,
    Session,
    Student,
)

from coderdojochi.util import str_to_bool

User = get_user_model()


@admin.register(User)
class UserAdmin(ImportExportActionModelAdmin):
    list_display = (
        'email',
        'first_name',
        'last_name',
        'role',
        'date_joined',
        'last_login',
        'is_active',
        'is_staff',
        'is_superuser',
    )

    list_filter = (
        'role',
        'is_active',
        'is_staff',
        'date_joined',
    )

    ordering = (
        '-date_joined',
    )

    date_hierarchy = 'date_joined'

    search_fields = (
        'first_name',
        'last_name',
        'email',
    )

    view_on_site = False

    filter_horizontal = (
        'groups',
        'user_permissions',
    )

    readonly_fields = (
        'password',
        'last_login',
    )

    change_form_template = 'loginas/change_form.html'


@admin.register(Mentor)
class MentorAdmin(ImportExportMixin, ImportExportActionModelAdmin):

    list_display = (
        'user',
        'get_first_name',
        'get_last_name',
        'created_at',
        'updated_at',
        'active',
        'public',
        'background_check',
        'avatar_approved',
    )

    list_filter = (
        'active',
        'public',
        'background_check',
        'avatar_approved',
    )

    ordering = (
        '-created_at',
    )

    date_hierarchy = 'created_at'

    search_fields = (
        'user__first_name',
        'user__last_name',
        'user__username',
        'user__email'
    )

    def view_on_site(self, obj):
        return obj.get_absolute_url()

    def get_first_name(self, obj):
        return obj.user.first_name
    get_first_name.short_description = 'First Name'
    get_first_name.admin_order_field = 'user__first_name'

    def get_last_name(self, obj):
        return obj.user.last_name
    get_last_name.short_description = 'First Name'
    get_last_name.admin_order_field = 'user__last_name'


class GuardianImportResource(resources.ModelResource):
    first_name = Field(attribute='first_name', column_name='first_name')
    last_name = Field(attribute='last_name', column_name='last_name')
    email = Field(attribute='email', column_name='email')
    phone = Field(attribute='phone', column_name='phone')
    zip = Field(attribute='zip', column_name='zip')

    def get_or_init_instance(self, instance_loader, row):
        """
        Either fetches an already existing instance or initializes a new one.
        """
        try:
            instance = User.objects.get(email=row['email'])
        except User.DoesNotExist:
            return Guardian(user=User()), True
        else:
            return (Guardian.objects.get(user=instance), False)

    def import_obj(self, obj, data, dry_run):
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        email = data.get('email')
        zip = data.get('zip')
        phone = data.get('phone')
        if obj.pk:
            user = obj.user
        else:
            user = User(
                first_name=first_name,
                last_name=last_name,
                email=email,
                role='guardian',
                username=email,
            )

        obj.user = user
        obj.active = False
        obj.zip = zip
        obj.phone = phone
        if not dry_run:
            user.save()
            obj.user = user
            obj.save()

    class Meta:
        model = Guardian
        import_id_fields = ('phone',)
        fields = ('phone', 'zip')


@admin.register(Guardian)
class GuardianAdmin(ImportExportMixin, ImportExportActionModelAdmin):
    list_display = (
        # 'user',
        'get_first_name',
        'get_last_name',
        # 'phone',
        # 'zip',
        'get_student_count',
        'created_at',
        'updated_at',
    )

    list_filter = (
        'zip',
    )

    ordering = (
        '-created_at',
    )

    search_fields = (
        'user__first_name',
        'user__last_name',
        'user__username',
    )

    date_hierarchy = 'created_at'

    view_on_site = False

    # Import settings
    resource_class = GuardianImportResource

    def get_queryset(self, request):
        qs = super(GuardianAdmin, self).get_queryset(request)
        qs = qs.annotate(Count('student'))
        return qs

    def get_first_name(self, obj):
        return obj.user.first_name
    get_first_name.short_description = 'First Name'
    get_first_name.admin_order_field = 'user__first_name'

    def get_last_name(self, obj):
        return obj.user.last_name
    get_last_name.short_description = 'Last Name'
    get_last_name.admin_order_field = 'user__last_name'

    def get_student_count(self, obj):
        return obj.student__count
    get_student_count.short_description = '# of Students'
    get_student_count.admin_order_field = 'student__count'


class StudentResource(resources.ModelResource):
    first_name = Field(attribute='first_name', column_name='first_name')
    last_name = Field(attribute='last_name', column_name='last_name')
    guardian_email = Field(attribute='guardian_email',
                           column_name='guardian_email')
    birthday = Field(attribute='birthday', column_name='birthday')
    gender = Field(attribute='gender', column_name='gender')
    school_name = Field(attribute='school_name', column_name='school_name')
    school_type = Field(attribute='school_type', column_name='school_type')
    photo_release = Field(attribute='photo_release',
                          column_name='photo_release')
    consent = Field(attribute='consent', column_name='consent')

    def import_obj(self, obj, data, dry_run):
        guardian_email = data.get('guardian_email')

        obj.first_name = data.get('first_name')
        obj.last_name = data.get('last_name')
        obj.birthday = datetime.strptime(data.get('birthday', ''), '%m/%d/%Y')
        obj.gender = data.get('gender', '')
        obj.school_name = data.get('school_name', '')
        obj.school_type = data.get('school_type', '')
        obj.photo_release = str_to_bool(data.get('photo_release', ''))
        obj.consent = str_to_bool(data.get('consent', ''))
        obj.active = True

        try:
            obj.guardian = Guardian.objects.get(user__email=guardian_email)
        except Guardian.DoesNotExist:
            raise ImportError(
                u'guardian with email {} not found'.format(guardian_email)
            )

        if not dry_run:
            obj.save()

    class Meta:
        model = Student
        import_id_fields = ('first_name', 'last_name')
        fields = ('first_name', 'last_name')
        # fields = ()


@admin.register(Student)
class StudentAdmin(ImportExportMixin, ImportExportActionModelAdmin):
    list_display = (
        'first_name',
        'last_name',
        'gender',
        'guardian',
        'created_at',
        'updated_at',
        'active'
    )

    list_filter = (
        'gender',
    )

    filter_horizontal = (
        'race_ethnicity',
    )

    ordering = (
        'guardian',
    )

    search_fields = (
        'first_name',
        'last_name',
        'guardian__user__first_name',
        'guardian__user__last_name',
    )

    date_hierarchy = 'created_at'

    view_on_site = False

    # Import settings
    resource_class = StudentResource


@admin.register(Course)
class CourseAdmin(ImportExportMixin, ImportExportActionModelAdmin):
    list_display = (
        'code',
        'title',
        'slug',
        'created_at',
        'updated_at',
    )

    list_filter = (
        'code',
    )

    ordering = (
        'created_at',
    )

    view_on_site = False


@admin.register(Session)
class SessionAdmin(ImportExportMixin, ImportExportActionModelAdmin):
    list_display = (
        'course',
        'start_date',
        'end_date',
        'location',
        'capacity',
        'get_current_orders_count',
        'get_mentor_count',
        'active',
        'public',
        'announced_date'
    )

    list_filter = (
        'active',
        'public',
        'course__title',
        'location',
    )

    ordering = (
        '-start_date',
    )

    filter_horizontal = (
        'waitlist_mentors',
        'waitlist_students',
    )

    date_hierarchy = 'start_date'

    view_on_site = False

    def view_on_site(self, obj):
        return obj.get_absolute_url()

    def get_mentor_count(self, obj):
        return MentorOrder.objects.filter(session__id=obj.id).count()
    get_mentor_count.short_description = 'Mentors'

    def get_current_orders_count(self, obj):
        return obj.get_current_orders().count()
    get_current_orders_count.short_description = "Students"


@admin.register(Order)
class OrderAdmin(ImportExportMixin, ImportExportActionModelAdmin):
    list_display = (
        # 'id',
        'student',
        'guardian',
        'alternate_guardian',
        'session',
        # 'ip',
        'check_in',
        'created_at',
        'updated_at',
        'active',
        'week_reminder_sent',
        'day_reminder_sent',
    )

    list_filter = (
        'active',
        'check_in',
        # 'guardian',
        'student',
        'session',
    )

    ordering = (
        'created_at',
    )

    date_hierarchy = 'created_at'

    view_on_site = False


@admin.register(MentorOrder)
class MentorOrderAdmin(ImportExportMixin, ImportExportActionModelAdmin):
    # def session(obj):
    #     url = reverse(
    #         'admin:coderdojochi_session_change',
    #         args=(obj.session.id,)
    #     )
    #     return mark_safe('<a href="{0}">{1}</a>'.format(url, obj.session))

    # session.short_description = 'Session'
    # raw_id_fields = ('session',)
    # readonly_fields = (session, 'session',)

    list_display = (
        'mentor',
        'session',
        'ip',
        'check_in',
        'active',
        'week_reminder_sent',
        'day_reminder_sent',
        'created_at',
        'updated_at',
    )

    list_display_links = (
        'mentor',
    )

    list_filter = (
        'active',
        'check_in',
        'session',
        # 'mentor',
    )

    ordering = (
        'created_at',
    )

    search_fields = (
        'mentor__user__first_name',
        'mentor__user__last_name',
    )

    readonly_fields = (
        # 'mentor',
        # 'session',
        'ip',
        # 'check_in',
    )

    date_hierarchy = 'created_at'
    view_on_site = False


@admin.register(MeetingOrder)
class MeetingOrderAdmin(ImportExportMixin, ImportExportActionModelAdmin):
    list_display = (
        'mentor',
        'meeting',
        'ip',
        'check_in',
        'active',
        'week_reminder_sent',
        'day_reminder_sent',
        'created_at',
        'updated_at'
    )

    list_filter = (
        'active',
        'meeting',
        'check_in',
        'meeting__meeting_type',
    )

    ordering = (
        'created_at',
    )

    search_fields = (
        'mentor__user__first_name',
        'mentor__user__last_name',
    )

    date_hierarchy = 'created_at'

    view_on_site = False


@admin.register(MeetingType)
class MeetingTypeAdmin(ImportExportMixin, ImportExportActionModelAdmin):
    list_display = (
        'code',
        'title',
        'slug',
    )
    list_display_links = (
        'title',
    )
    view_on_site = False


@admin.register(Meeting)
class MeetingAdmin(ImportExportMixin, ImportExportActionModelAdmin):
    list_display = (
        'meeting_type',
        'start_date',
        'end_date',
        'location',
        'get_mentor_count',
        'public',
        'announced_date',
        'created_at'
    )

    list_filter = (
        'active',
        'public',
        'location',
        'meeting_type__title',
    )

    ordering = (
        '-start_date',
    )

    date_hierarchy = 'start_date'
    view_on_site = False

    def view_on_site(self, obj):
        return obj.get_absolute_url()

    def get_mentor_count(self, obj):
        return MeetingOrder.objects.filter(meeting__id=obj.id).count()
    get_mentor_count.short_description = 'Mentors'


@admin.register(EquipmentType)
class EquipmentTypeAdmin(ImportExportMixin, ImportExportActionModelAdmin):
    view_on_site = False


@admin.register(Equipment)
class EquipmentAdmin(ImportExportMixin, ImportExportActionModelAdmin):
    list_display = (
        'uuid',
        'asset_tag',
        'equipment_type',
        'make',
        'model',
        'condition',
        'last_system_update_check_in',
        'last_system_update',
        'force_update_on_next_boot',
    )

    list_filter = (
        'condition',
        'equipment_type',
        'make',
        'model',
    )

    ordering = (
        'uuid',
    )

    search_fields = (
        'uuid',
        'make',
        'model',
        'asset_tag',
    )

    readonly_fields = (
        'last_system_update_check_in',
        'last_system_update',
    )

    view_on_site = False


@admin.register(Donation)
class DonationAdmin(ImportExportMixin, ImportExportActionModelAdmin):
    list_display = (
        'first_name',
        'last_name',
        'email',
        'amount',
        'verified',
        'receipt_sent',
        'created_at',
        'updated_at',
    )

    list_filter = (
        'verified',
        'receipt_sent',
        'amount',
        'created_at',
    )

    ordering = (
        '-created_at',
    )

    search_fields = (
        'first_name',
        'last_name',
        'email',
    )

    date_hierarchy = 'created_at'

    view_on_site = False


@admin.register(Location)
class LocationAdmin(ImportExportMixin, ImportExportActionModelAdmin):
    view_on_site = False


@admin.register(RaceEthnicity)
class RaceEthnicityAdmin(ImportExportMixin, ImportExportActionModelAdmin):
    pass
