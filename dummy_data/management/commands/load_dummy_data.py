from django.core.management.base import BaseCommand
from django.apps import apps
from django.contrib.auth.models import User

from dummy_data.models import DummyData

import csv


class Command(BaseCommand):
    """
    Management command to load dummy data

    Dummy data files are csv files present in each app.
    Each data is tracked through a database model for future
    reference.
    This helps prevent that no data is loaded multiple times in future.
    """
    def handle(self, *args, **kwargs):
        self.stdout.write('Loading users')
        self.load('user', 'User', User, User.objects.create_user)

        self.stdout.write('Loading projects and members')
        self.load('project', 'Project')
        self.load('project', 'ProjectMembership')

        self.stdout.write('Loading user groups')
        self.load('user_group', 'UserGroup')

        self.stdout.write('Loading leads')
        self.load('lead', 'Lead')

        self.stdout.write('Adding user groups to projects')
        self.load_manytomany('project', 'Project_UserGroup',
                             'user_groups')

        self.stdout.write('Done')

    def load_manytomany(self, app_name1, filename, field, model1=None):
        """
        Load manytomany items

        model1 is first model where the ManyToManyField is present and
        model2 is the related second model.

        app_name1 - App where the file is present
                    Unless model1 is specified expicity, this app
                    is by default considered the one where model1 is present
        filename  - Filename of csv file without extension
                    Should be format Model1_Model2
        field     - ManyToManyField in model1
        model1    - Optional, explicit model for model1
                    Useful when model1 is not actually present in app
                    where the csv file is present.
                    Useful for using models like auth.models.User
        """

        # Split he filename into model_names
        model_names = filename.split('_')

        # Find model1, model2 and the referential model_names
        # to use with DummyData
        if not model1:
            model1 = apps.get_model(app_name1, model_names[0])

        model2 = model1._meta.get_field(field).related_model
        app_name2 = model2._meta.app_label

        model_name1 = '{}.{}'.format(app_name1, model_names[0])
        model_name2 = '{}.{}'.format(app_name2, model_names[1])

        # Read the csv file
        path = '{}/dummy_data/{}.csv'.format(app_name1, filename)

        with open(path) as csvfile:
            reader = csv.DictReader(csvfile)

            # Get each row in the file
            for row in reader:

                # The first object where the ManyToManyField exists
                db_id1 = DummyData.objects.get(
                    model_name=model_name1,
                    data_id=row[model_names[0]],
                ).db_id
                obj1 = model1.objects.get(id=db_id1)

                # The second object to be added to the many-to-many collection
                db_id2 = DummyData.objects.get(
                    model_name=model_name2,
                    data_id=row[model_names[1]],
                ).db_id
                obj2 = model2.objects.get(id=db_id2)

                # Add obj2 to obj1.field
                getattr(obj1, field).add(obj2)

    def load(self, app_name, filename, model=None, create_obj=None):
        """
        Load objects from a csv file

        app_name    -   App where the csv file is present
                        If explicit model is not set, this is also
                        the app where the model is assumed to be present
        filename    -   Filename of csv file without extension
                        Is explicit model is not set, this is also assumed
                        to be the name of model
        model       -   Optional explicit model to use
                        Useful when model is not actually present in the app
                        where the csv file is present
                        Useful for using models like auth.models.User
        create_obj  -   Optional, explicit create_model function to use
                        Useful for cases like auth.models.User
                        By default model.objects.create(...) is used
        """

        # If model not provided, get it from the app name and filename
        if not model:
            model = apps.get_model(app_name, filename)
        model_name = '{}.{}'.format(app_name, filename)

        # Read the file
        path = '{}/dummy_data/{}.csv'.format(app_name, filename)

        with open(path) as csvfile:
            reader = csv.DictReader(csvfile)

            # Get each object as a row
            for row in reader:

                # First resolve the foreign keys
                self.resolve_foreign_keys(model, row)

                # See if this one's been already added
                existing = DummyData.objects.filter(
                    model_name=model_name,
                    data_id=row['id']
                )

                obj = None
                if existing.count() > 0:
                    # If existing, just get the references
                    dd = existing[0]
                    try:
                        obj = model.objects.get(id=dd.db_id)
                    except:
                        dd.delete()
                if not obj:
                    # If not, create new one
                    dd = DummyData(
                        model_name=model_name,
                        data_id=row['id'],
                    )

                    # We don't want to use this id
                    # This is only used for reference in the
                    # dummy data files
                    del row['id']

                    if create_obj:
                        obj = create_obj(**row)
                    else:
                        obj = model.objects.create(**row)

                # Finally save the dummy data object in the database
                # for future reference
                dd.db_id = obj.id
                dd.save()

    def resolve_foreign_keys(self, model, row):
        """
        Replace the foreign related values in the row
        with actual objects

        Foreign related values are written in format:
        foreign_app.foregin_model.dummy_data_id
        """

        # For each foreign key field in the model,
        for field in model._meta.fields:
            if field.get_internal_type() == 'ForeignKey':

                # If the field exists in the row,
                if field.name in row:
                    value = row[field.name]

                    # Either replace with null value
                    # or with actual object depending on the
                    # value provided

                    if value == 'null':
                        row[field.name] = None
                    else:
                        splits = value.split('.')
                        model_name = '{}.{}'.format(splits[0], splits[1])

                        db_id = DummyData.objects.get(
                            data_id=splits[2],
                            model_name=model_name,
                        ).db_id

                        row[field.name] = field.rel.to.objects.get(
                            id=db_id
                        )
