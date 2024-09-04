from django.db import models
from django.utils.translation import gettext_lazy as _

# Create your models here.

# class CarouselSlide(models.Model):
#     slide = models.ImageField(_("Carousel Slide Image"), upload_to="images/carousel/%Y/%m/%d")
#     html = models.TextField(_("Slide HTML"), blank=True)
#     order = models.PositiveSmallIntegerField(_("Order"))
#     active = models.BooleanField(default=True)

# class TopBarFlash(models.Model):
#     html = models.TextField(_("Flash HTML"), blank=False)
#     active = models.BooleanField(default=True)

# class TopMenu(models.Model):
#     title = models.CharField(_("Menu Title"), max_length=255, blank=False)
    