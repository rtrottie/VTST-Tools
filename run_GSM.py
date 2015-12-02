#!/usr/bin/env python

import os
import jinja2

file_loc = os.environ['GSM_DIR']


with open('GSM-Submit.sh', 'w') as f:
    template = env.get_template('grad.jinja2.py')
    f.write(template.render(jinja_vars))