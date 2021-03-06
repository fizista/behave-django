"""
Test suite for behave-django.  See features folder for implementation.
Run it by

- ``python setup.py -q test -v`` or
- ``python manage.py test`` or
- ``python tests.py`` (preferred)
"""
from django.core.management import call_command
from mock import patch
from os import linesep as LF
from subprocess import PIPE, Popen
import django
import os
import unittest


def run_silently(command):
    """Run a shell command and return both exit_status and console output."""
    command_args = command.split()
    process = Popen(command_args, stdout=PIPE, stderr=PIPE, stdin=PIPE)
    stdout, stderr = process.communicate()
    output = (stdout.decode('UTF-8') + LF +
              stderr.decode('UTF-8')).strip()
    return process.returncode, output


def run_management_command(command, *args, **kwargs):
    try:
        # required only since version 1.7
        django.setup()
    except AttributeError:
        pass
    call_command(command, *args, **kwargs)


class BehaveDjangoTestCase(unittest.TestCase):

    def setUp(self):
        # NOTE: this may potentially have side-effects, making tests pass
        # that would otherwise fail, because it *always* overrides which
        # settings module is used.
        os.environ['DJANGO_SETTINGS_MODULE'] = 'test_project.settings'

    def test_flake8(self):
        exit_status, output = run_silently('flake8')
        assert exit_status == 0

    def test_additional_management_command_options(self):
        exit_status, output = run_silently('python manage.py behave --help')
        assert exit_status == 0
        assert (LF + '  --use-existing-database' + LF) in output

    @patch('behave_django.management.commands.behave.behave_main', return_value=0)  # noqa
    @patch('sys.exit')
    def test_command_should_exit_zero_if_passing(self,
                                                 mock_sys_exit,
                                                 mock_behave_main):
        # If the exit status returned by behave_main is 0, make sure sys.exit
        # does not get called
        run_management_command('behave', dry_run=True)
        assert not mock_sys_exit.called

    @patch('behave_django.management.commands.behave.behave_main', return_value=1)  # noqa
    @patch('sys.exit')
    def test_command_should_exit_nonzero_if_failing(self,
                                                    mock_sys_exit,
                                                    mock_behave_main):
        # If the exit status returned by behave_main is anything other than 0,
        # make sure sys.exit gets called with the exit code

        # Dry run to not create the database for faster tests
        run_management_command('behave', dry_run=True)
        mock_sys_exit.assert_called_once_with(1)

    @patch('behave_django.management.commands.behave.behave_main', return_value=0)  # noqa
    @patch('behave_django.management.commands.behave.ExistingDatabaseTestRunner')  # noqa
    def test_dont_create_db_with_dryrun(self,
                                        mock_existing_database_runner,
                                        mock_behave_main):
        run_management_command('behave', dry_run=True)
        mock_behave_main.assert_called_once_with(args=[])
        mock_existing_database_runner.assert_called_once_with()

    @patch('behave_django.management.commands.behave.behave_main', return_value=0)  # noqa
    @patch('behave_django.management.commands.behave.ExistingDatabaseTestRunner')  # noqa
    def test_dont_create_db_with_useexistingdb(self,
                                               mock_existing_database_runner,
                                               mock_behave_main):
        run_management_command('behave', use_existing_database=True)
        mock_behave_main.assert_called_once_with(args=[])
        mock_existing_database_runner.assert_called_once_with()


if __name__ == '__main__':
    unittest.main()
