
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import pre_save
from django.dispatch import receiver
from unidecode import unidecode

def now():
    return timezone.localtime(timezone.now())

class Project(models.Model):

    name = models.CharField(
        verbose_name=_('Name'),
        max_length=256,
        blank=True,
    )

    created_at = models.DateTimeField(
        verbose_name=_('Created at'),
        auto_now_add=True
    )

    created_by = models.ForeignKey(
        verbose_name=_('Created by'),
        to=settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        default=None
    )

    project_articles_sum = models.IntegerField(
        verbose_name=_("Amount of Project's articles"),
        blank=True,
        null=True,
    )


    project_basestone_keyword_sum = models.IntegerField(
        verbose_name=_('Basestone Keyword Amount'),
        blank=True,
        null=True,
    )
    

    project_stellar_keyword_sum = models.IntegerField(
        verbose_name=_('Stellar Keyword Amount'),
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.name

    slug = models.SlugField(unique=True, null=True, blank=True)


def create_slug(instance, new_slug=None):
    '''
        Recursive function to check whether slug and instance has been created
        Question: whether we need this?

        @receiver(pre_save, sender=Project)
        def slug_generator(sender, instance, *args, **kwargs):
            if not instance.slug:
                instance.slug = create_slug(instance)
    '''
    slug = slugify(instance.name)
    if new_slug is not None:
        slug = new_slug
    querySet = Article.objects.filter(slug=slug).order_by("-id")
    exists = querySet.exists()
    if exists:
        new_slug = f"{slug}-{querySet.first().id}"
        return create_slug(instance, new_slug=new_slug)
    return slug



@receiver(pre_save, sender=Project)
def slug_generator(sender, instance, *args, **kwargs):
    slug = slugify(unidecode(instance.name))
    exists = Project.objects.filter(slug=slug).exists()
    if exists:
        slug = f"{slug}-{instance.id}"
    instance.slug = slug