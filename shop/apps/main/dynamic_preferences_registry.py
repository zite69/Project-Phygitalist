from dynamic_preferences.types import BooleanPreference, StringPreference, ChoicePreference
from dynamic_preferences.preferences import Section
from dynamic_preferences.registries import global_preferences_registry
from dynamic_preferences.users.registries import user_preferences_registry

# we create some section objects to link related preferences together

general = Section('general')

# We start with a global preference
@global_preferences_registry.register
class SiteTitle(StringPreference):
    section = general
    name = 'title'
    default = 'Zite69 - Social Marketplace'
    required = False

@global_preferences_registry.register
class MaintenanceMode(BooleanPreference):
    section = Section('sysadmin')
    name = 'maintenance_mode'
    verbose_name = 'Maintenance Mode'
    help_text = 'Sets the website in maintenance mode, making it inaccessible for users and only accessible to staff and administrators'
    default = False

# now we declare a per-user preference
@user_preferences_registry.register
class LanguagePreference(ChoicePreference):
    choices = [
        ('', 'Not Set'),
        ('--', 'None'),
        ('ML', 'Malayalam'),
        ('KN', 'Kannada'),
        ('TA', 'Tamil'),
        ('TE', 'Telugu'),
        ('HI', 'Hindi')
    ]

    help_text = 'Please select your second preferred language'
    verbose_name = 'Second Language Preferrence'
    name = 'second_language'
    required = False
    default = ''
