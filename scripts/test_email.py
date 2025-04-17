from django.conf import settings
from django.template.loader import get_template
from django.template.base import VariableNode
from shop.apps.main.utils.email import send_email

def get_var_nodes(node):
    ret = set()
    if hasattr(node, 'nodelist'):
        for n in node.nodelist:
            if n.__class__ == VariableNode:
                ret.add(n.token.contents)
            if hasattr(n, 'nodelist'):
                ret.update(get_var_nodes(n))
    return ret

def run(*args):
    cmd = args[0]
    temp = args[1]
    template_name = f"email/{temp}.html"
    template = get_template(template_name)
    variables = set()
    for n in template.template.nodelist:
        variables.update(get_var_nodes(n))
    base = get_template(template.template.nodelist[0].parent_name.token.strip("'"))
    for n in base.template.nodelist:
        variables.update(get_var_nodes(n))
    variables = list(filter(lambda n: n != 'base_uri', variables))
    if cmd == 'list':
        print(f"Variables inside {temp}.html: {variables}")
    elif cmd == 'send':
        ctx = {}
        ctx['base_uri'] = 'https://www.zite69.com'
        if len(variables) + 2 != len(args):
            print(f"Please specify all variable values: {variables}")
            return
        for i, v in enumerate(variables):
            if '.' not in v:
                ctx[v] = args[2+i]
            else:
                obj, prop = v.split(".")
                if obj not in ctx:
                    ctx[obj] = {}
                ctx[obj][prop] = args[2+i]
        ctx['template'] = template_name
        resp = send_email(settings.SEND_TEST_EMAIL, **ctx)
        print(resp)
