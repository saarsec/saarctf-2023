from django.db import models
import uuid


class Post(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    pass_token = models.CharField(max_length=32)
    text = models.TextField()
    stamp = models.IntegerField()

    def save(self, *args, **kwargs):
        super(Post, self).save(*args, **kwargs)
        #print('Save method executed!')

    def __str__(self):
        return f"{self.id} | {self.pass_token} | {self.text} | {self.time} \n"

