from django.utils.html import strip_tags, strip_entities

from haystack import indexes, site
from memberships.models import App, AppEntry, Membership
from perms.models import ObjectPermission

class MembershipIndex(indexes.RealTimeSearchIndex):
    text = indexes.CharField(document=True, use_template=True)
    corporate_membership_id = indexes.BooleanField(model_attr='corporate_membership_id')

    # tendenci_base fields
    allow_anonymous_view = indexes.BooleanField(model_attr='allow_anonymous_view')
    allow_user_view = indexes.BooleanField(model_attr='allow_user_view')
    allow_member_view = indexes.BooleanField(model_attr='allow_member_view')
    allow_anonymous_edit = indexes.BooleanField(model_attr='allow_anonymous_edit')
    allow_user_edit = indexes.BooleanField(model_attr='allow_user_edit')
    allow_member_edit = indexes.BooleanField(model_attr='allow_member_edit')
    creator = indexes.CharField(model_attr='creator')
    creator_username = indexes.CharField(model_attr='creator_username')
    owner = indexes.CharField(model_attr='owner')
    owner_username = indexes.CharField(model_attr='owner_username')
    create_dt = indexes.DateTimeField(model_attr='create_dt')
    update_dt = indexes.DateTimeField(model_attr='update_dt')
    status = indexes.IntegerField(model_attr='status')
    status_detail = indexes.CharField(model_attr='status_detail')

    # permission
    who_can_view = indexes.CharField()

    def prepare_who_can_view(self, obj):
        users = ObjectPermission.objects.who_has_perm('memberships.view_membership', obj)

        if not users:
            users = []

        return ','.join([u.username for u in users])


class MemberAppIndex(indexes.RealTimeSearchIndex):
    text = indexes.CharField(document=True, use_template=True)
    name = indexes.CharField(model_attr='name')
    description = indexes.CharField(model_attr='description')

    # authority fields
    allow_anonymous_view = indexes.BooleanField(model_attr='allow_anonymous_view')
    allow_user_view = indexes.BooleanField(model_attr='allow_user_view')
    allow_member_view = indexes.BooleanField(model_attr='allow_member_view')
    allow_anonymous_edit = indexes.BooleanField(model_attr='allow_anonymous_edit')
    allow_user_edit = indexes.BooleanField(model_attr='allow_user_edit')
    allow_member_edit = indexes.BooleanField(model_attr='allow_member_edit')
    creator = indexes.CharField(model_attr='creator')
    creator_username = indexes.CharField(model_attr='creator_username')
    owner = indexes.CharField(model_attr='owner')
    owner_username = indexes.CharField(model_attr='owner_username')
    status = indexes.IntegerField(model_attr='status')
    status_detail = indexes.CharField(model_attr='status_detail')

    # permission
    who_can_view = indexes.CharField()
    
    def prepare_who_can_view(self, obj):
        users = ObjectPermission.objects.who_has_perm('articles.view_article', obj)
        user_list = []
        if users:
            for user in users:
                user_list.append(user.username)
            return ','.join(user_list)
        else: 
            return ''

    def prepare_description(self, obj):
        description = obj.description
        description = strip_tags(description)
        description = strip_entities(description)
        return description

class MemberAppEntryIndex(indexes.RealTimeSearchIndex):
    text = indexes.CharField(document=True, use_template=True)
    entry_time = indexes.DateTimeField(model_attr='entry_time')

site.register(Membership, MembershipIndex)
site.register(App, MemberAppIndex)
site.register(AppEntry, MemberAppEntryIndex)