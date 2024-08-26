from tortoise import fields
from tortoise.models import Model


class Connection(Model):
    id = fields.IntField(pk=True)

    user_id = fields.IntField()
    username = fields.CharField(null=True, max_length=16)

    is_banned = fields.BooleanField(default=False)
    ban_reason = fields.CharField(null=True, max_length=64)

    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
