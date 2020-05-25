#!/usr/bin/python

import os
import json
import subprocess

import argparse

parser = argparse.ArgumentParser(description='Create zip files for aws lambda')

parser.add_argument('dir', type=str, default=os.getcwd(), nargs='?',
                    help="Directory that contains function and function config")
parser.add_argument('--config', type=str, default='lambda_config.json',
                    help='Lambda config json file. Defaults to "lambda_config.json"')
parser.add_argument('--update-function', action='store_true',
                    help='Just update the function file in the zip. Skips all other processes.')
parser.add_argument('--update-extra-modules', action='store_true',
                    help='Just update the extra files in the zip. Skips all other processes.')


def validate_config(args):
    return True


def install_requirements(args):
    """Takes in config and installs requremeints and zips them"""
    print("Preparing installing requirements...")
    config = args.config
    if not config.get('requirements_file') and not config.get('requirements'):
        return
    if config['requirements_file']:
        subprocess.call(['pip', 'install', '--target', args.package_target, '-r', config['requirements_file']])
    elif config['requirements']:
        subprocess.call(['pip', 'install', '--target', args.package_target, *config['requirements']])


def zip_requirements(args):
    # Zip the package directory
    print('TARGET', args.package_target)
    print('Zipping requirements...')
    os.system(f'cd {args.package_target} && echo `pwd` && zip -r9 {args.zip_path} .')
    print('Done')


def add_extra_modules(args):
    print('Adding extra modules...')
    config = args.config
    project_root = config.get('project_root', os.getcwd())
    extra_modules = config.get('extra_modules') or []
    for each in extra_modules:
        module_path = os.path.join(project_root, each)
        if os.path.isdir(module_path):
            os.system(f'cd `dirname {module_path}` && zip -r9 -g {args.zip_path} {each}')
        else:
            os.system(f'cd `dirname {module_path}` && zip -g {args.zip_path} `basename {module_path}`')
    print('Done')


def add_function_file(args):
    print('Adding function file...')
    config = args.config
    function_file = config['function_file']
    function_path = os.path.join(args.dir, function_file)
    os.system(f'cd `dirname {function_path}` && zip -g {args.zip_path} {function_file}')
    print('Done')


def run_all(args):
    install_requirements(args)
    zip_requirements(args)
    add_extra_modules(args)
    add_function_file(args)

    print('Lambda function and its dependencies have been zipped to "function.zip"')
    print('You may now upload the zip file')


def main():
    args = parser.parse_args()
    abs_path_root = os.path.abspath(args.dir)
    config_path = os.path.join(abs_path_root, args.config)
    config = json.load(open(config_path))

    args.config = config
    args.package_target = os.path.join(abs_path_root, 'package')
    args.zip_path = os.path.join(abs_path_root, 'function.zip')
    validate_config(args)

    if args.update_function:
        add_function_file(args)
        print("Function file has been updated in the zip.")
    if args.update_extra_modules:
        add_extra_modules(args)

    if not args.update_function and not args.update_extra_modules:
        print("Running all steps")
        run_all(args)


if __name__ == '__main__':
    main()
