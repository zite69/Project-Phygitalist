from django.conf import settings
from django.template.loader import get_template
from django.template.base import VariableNode
from shop.apps.main.utils.email import send_email

def get_var_nodes(node):
    ret = []
    for n in node.nodelist:
        if n.__class__ == VariableNode:
            ret.append(n)
        if hasattr(n, 'nodelist'):
            ret.extend(get_var_nodes(n))
    return ret

def run(*args):
    cmd = args[0]
    temp = args[1]
    if cmd == 'list':
        template = get_template(f"email/{temp}.html")
        variables = []
        for n in template.template.nodelist:
            variables.extend(get_var_nodes(n))
        variables = [v.token.contents for v in variables]
        print(f"Variables inside {temp}.html: {variables}")
    elif cmd == 'send':
        template_name = f"email/{temp}.html"
        template = get_template(template_name)
        variables = []
        for n in template.template.nodelist:
            variables.extend(get_var_nodes(n))
        variables = [v.token.contents for v in variables]
        ctx = {}
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
