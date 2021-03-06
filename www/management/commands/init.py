# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# Copyright 2014, Cercle Informatique ASBL. All rights reserved.
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at
# your option) any later version.
#
# This software was made by hast, C4, ititou at UrLab, ULB's hackerspace

from django.core.management.base import BaseCommand
from django.db import transaction
from users.models import User
from getpass import getpass, getuser
from optparse import make_option
from graph.models import Category, Course, CourseInfo
from polydag.models import Keyword
from datetime import datetime
import json
from shutil import copy
import os
from os.path import join
from www import settings


class Command(BaseCommand):
    drops = [u"Niveau dans le cycle*", u"Lieu d’enseignement*", u"Cycle*",
             u"Faculté gestionnaire*", u"Institution organisatrice*",
             u"Langue d'évaluation*", u"Horaire*", u"Discipline*",
             u"Contenu du cours*", u"Priorités de l'enseignant",
             u"Autres pré-requis", u"Objectifs du cours et compétences visées*",
             u"Syllabus*"]
    NOW = datetime.now()
    USER = None

    to_ulb = lambda self, n: n[0:4].upper() + "_" + n[5].upper() + n[7:]

    help = 'Initialize p402 for developpment'
    option_list = BaseCommand.option_list + (
        make_option('--netid', action='store', dest='netid', default=None, help='default netid'),
        make_option('--password', action='store', dest='password', default=None, help='default password'),
        make_option('--first-name', action='store', dest='first_name', default=None, help='default first name'),
        make_option('--last-name', action='store', dest='last_name', default=None, help='default last name'),
        make_option('--prod', action='store_true', dest='production', default=None, help='production init'),
    )

    def add_keywords(self):
        Keyword.objects.create(name="labo")
        Keyword.objects.create(name="tp")
        Keyword.objects.create(name="examen")
        Keyword.objects.create(name="résumé")
        Keyword.objects.create(name="formulaire")
        Keyword.objects.create(name="référence")
        Keyword.objects.create(name="projet")
        Keyword.objects.create(name="consignes")

        Keyword.objects.create(name="slides")
        Keyword.objects.create(name="syllabus")

        Keyword.objects.create(name="officiel")
        Keyword.objects.create(name="corrigé")
        Keyword.objects.create(name="points")

    def createCourse(self, parentNode, slug):
        try:
            course = Course.objects.get(slug=slug)
        except:
            ULBInfos = self.courseList[self.to_ulb(slug)]
            name = slug.upper()
            infos = []
            for cat, content in ULBInfos.iteritems():
                if content == "" or cat in self.drops:
                    continue
                if cat == u"Construction de la note, pondération des différentes activités*":
                    cat = "Note"
                if cat == u"Langue d'enseignement*":
                    cat = "Langue"
                if cat == u"Nom":
                    cat = "Nom"
                    name = content
                if cat[-1] == "*":
                    cat = cat[:-1]
                infos.append({"name": cat, "value": content})
            course = Course.objects.create(
                name=name, slug=slug,
                description=json.dumps(ULBInfos)
            )
            CourseInfo.objects.create(
                course=course, infos=json.dumps(infos),
                date=self.NOW
            )
        parentNode.add_child(course)
        self.stdout.write('.', ending='')
        self.stdout.flush()

    def walk(self, jsonTree, parentNode):
        for key in jsonTree:
            val = jsonTree[key]
            if key.lower() == 'course':
                for slug in val:
                    self.createCourse(parentNode, slug)
            else:
                category = Category.objects.create(name=key, description="Magic !")
                parentNode.add_child(category)
                self.stdout.write('#', ending='')
                self.stdout.flush()
                self.walk(val, category)

    def handle(self, *args, **options):
        self.stdout.write('Creating user\n')
        user = User()

        if not options["production"]:
            netid = raw_input("NetID (default: %s): " % getuser()) if options["netid"] is None else options["netid"]
            if not netid:
                netid = getuser()
            user.netid = netid
            password = getpass("Password (default: 'test'): ") if options["password"] is None else options["password"]
            if not password:
                password = 'test'
            first_name = raw_input("Firstname (default: John): ") if options["first_name"] is None else options["first_name"]
            if not first_name:
                first_name = "John"
            last_name = raw_input("Lastname (default: Smith): ") if options["last_name"] is None else options["last_name"]
            if not last_name:
                last_name = "Smith"
            user.first_name = first_name
            user.last_name = last_name
            user.set_password(password)
            user.email = 'gaston@dupuis.be'
            user.photo = 'gif'
            user.is_staff = True
        else:
            user.netid = "tverhaegen"
            user.first_name = "Théodore"
            user.last_name = "Verhaegen"
            user.set_password("STV2014")
            user.email = 'p402@urlab.be'
            user.photo = 'png'
            user.is_staff = True

        user.save()

        IMG_S_DIR = join(settings.BASE_DIR, 'www', 'management', 'commands')
        IMG_D_DIR = join(settings.BASE_DIR, 'media', 'profile')

        if not os.path.exists(IMG_D_DIR):
            os.makedirs(IMG_D_DIR)

        if not options["production"]:
            copy(join(IMG_S_DIR, 'gaston.gif'), join(IMG_D_DIR, netid + '.gif'))

        if not options["production"]:
            # Second user for tests
            user2 = User()
            user2.netid = "blabevue"
            user2.first_name = "Bertrand"
            user2.last_name = "Labévue"
            user2.set_password(password)
            user2.email = 'bertrand@labevue.be'
            user2.photo = 'gif'
            user2.save()

        if not options["production"]:
            copy(join(IMG_S_DIR, 'labevue.gif'), join(IMG_D_DIR, 'blabevue.gif'))
            self.stdout.write("Second user {} with password {} created\n".format(
                user2.netid, password
            ))
        else:
            copy(join(IMG_S_DIR, 'theodore.png'), join(IMG_D_DIR, 'tverhaegen.png'))

        tree = json.load(open('parsing/tree.json'))
        self.courseList = json.load(open('parsing/cours.json'))
        Root = Category.objects.create(name='P402', description='Bring back real student cooperation !')
        
        with transaction.atomic():
            self.walk(tree, Root)
            self.stdout.write("\n")
            self.add_keywords()
