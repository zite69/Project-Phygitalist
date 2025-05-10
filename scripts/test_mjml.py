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
    template_name = f"email/mjml/{temp}.html"
    template = get_template(template_name)
    variables = set()
    for n in template.template.nodelist:
        variables.update(get_var_nodes(n))
    # base_name = template.template.nodelist[0].parent_name.token.strip("'").strip('"')
    # print(base_name)
    # base = get_template(base_name)
    # for n in base.template.nodelist:
    #     variables.update(get_var_nodes(n))
    variables = list(filter(lambda n: n != 'base_uri' and n != 'block.super' , variables))
    if cmd == 'list':
        print(f"Variables inside {temp}.html: {variables}")
    elif cmd == "send":
        ctx = {}
        ctx['user'] = {}
        ctx['user']['get_full_name'] = 'Arun Kumar'
        ctx['template'] = template_name
        ctx['subject'] = 'Add a product'
        # ctx['to'] = 'arunkakorp@gmail.com'

        resp = send_email('arunkakorp@gmail.com', **ctx)
        print("Got response: ", resp)
