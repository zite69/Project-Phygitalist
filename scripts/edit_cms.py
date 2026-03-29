from djangocms_alias.models import Alias, AliasContent
from djangocms_text_ckeditor.models import Text  # or whatever plugin model
import sys
import re

def run(*args):
    code = args[0]
    pattern = args[1]
    sub = args[2]
    # 1. Get the alias by static_code
    alias = Alias.objects.get(static_code=code)

    # 2. Get the content for a language
    content = alias.contents.get(language='en')

    # 3. Get the placeholder
    placeholder = content.placeholders.get(slot='content')

    plugin = placeholder.get_plugins().get(plugin_type='TextPlugin')
    text_instance = plugin.get_plugin_instance()[0]

    print("old text:")
    print(text_instance.body)
    text_instance.body = re.sub(pattern, sub, text_instance.body)
    text_instance.save()
    print("new text:")
    print(text_instance.body)
