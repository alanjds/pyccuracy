#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os.path import abspath, dirname, join, exists
import warnings
from optparse import make_option

from django.core.management.base import BaseCommand
from django.conf import settings

from pyccuracy.pyccuracy_console import main as run_pyccuracy
from pyccuracy.common import locate

class Command(BaseCommand):
    help = "Runs pyccuracy tests for all apps (EXPERIMENTAL)"
    option_list = BaseCommand.option_list + (
        make_option("-s", "--scenario", dest=u"scenario", default=None, help=u"Number (index) for the scenario to be executed. Use commas for several scenarios. I.e.: -s 3,6,7 or --scenario=3,6,7."),
        make_option("-l", "--loglevel", dest=u"loglevel", default=1, help=u"Verbosity: 1, 2 ou 3."),
        make_option("-u", "--baseurl", dest=u"baseurl", default=u"http://localhost:8000", help=u"Base Url for acceptance tests. Defaults to http://localhost:8000."),
        make_option("-p", "--pattern", dest=u"pattern", default=u"*.acc", help=u"Pattern (wildcard) to be used to find acceptance tests."),
        make_option("-b", "--browser", dest=u"browser", default=u"firefox", help=u"Browser that will be used to run the tests."),
        make_option("-w", "--workers", dest=u"workers", default=1, help=u"Number of tests to be run in parallel."),
        make_option("-c", "--language", dest=u"language", default='en-us', help=u"Language to run the tests in. Defaults to 'en-us'."),
    )
    
    def locate_resource_dirs(self, complement, pattern="*.*", recursive=True):
        dirs = []
        for app in settings.INSTALLED_APPS:
            fromlist = ""

            if len(app.split("."))>1:
                fromlist = ".".join(app.split(".")[1:])

            if app.startswith('django'):
                continue

            module = __import__(app, fromlist=fromlist)
            app_dir = abspath("/" + "/".join(module.__file__.split("/")[1:-1]))

            resource_dir = join(app_dir, complement)

            if exists(resource_dir) and locate(resource_dir, pattern, recursive):
                dirs.append(resource_dir)

        return dirs

    def handle(self, *args, **options):
        if args:
            selenium_host_and_port = args[0].split(':')
            if len(selenium_host_and_port) > 1:
                (seleniumn_host, selenium_port) = selenium_host_and_port
            else:
                selenium_host = selenium_host_and_port[0]
                selenium_port = 4444
        else:
            selenium_host = "localhost"
            selenium_port = 4444

        dir_template = "-d %s"
        action_template = "-A %s"
        page_template = "-P %s"

        pattern = options['pattern']

        dirs = self.locate_resource_dirs("tests/acceptance", pattern)

        action_pages_dirs = self.locate_resource_dirs("tests/acceptance", "__init__.py")
        pages_templates = " ".join([page_template % dirname for dirname in action_pages_dirs])
        actions_templates = " ".join([action_template % dirname for dirname in action_pages_dirs])

        dir_templates = " ".join([dir_template % dirname for dirname in dirs])

        pyccuracy_arguments = []

        pyccuracy_arguments.append("-u")
        pyccuracy_arguments.append(options["baseurl"])
        pyccuracy_arguments.extend(dir_templates.split(" "))
        pyccuracy_arguments.extend(actions_templates.split(" "))
        pyccuracy_arguments.extend(pages_templates.split(" "))
        pyccuracy_arguments.append("-p")
        pyccuracy_arguments.append(options["pattern"])
        pyccuracy_arguments.append("-l")
        pyccuracy_arguments.append(options["language"])
        pyccuracy_arguments.append("-w")
        pyccuracy_arguments.append(options["workers"])
        pyccuracy_arguments.append("-v")
        pyccuracy_arguments.append(options["loglevel"])

        if options["scenario"]:
            pyccuracy_arguments.append("-s")
            pyccuracy_arguments.append(options["scenario"])

        pyccuracy_arguments.append("-b")
        pyccuracy_arguments.append(options["browser"])
        pyccuracy_arguments.append("selenium.server=%s" % selenium_host)
        pyccuracy_arguments.append("selenium.port=%s" % selenium_port)

        print u'***********************'
        print u'Running Pyccuracy Tests'
        print u'***********************'

        pyccuracy_arguments = [argument for argument in pyccuracy_arguments if argument != '' and argument is not None]

        ret_code = run_pyccuracy(pyccuracy_arguments)
        raise SystemExit(ret_code)
