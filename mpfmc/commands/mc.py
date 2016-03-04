"""Starts the MPF media controller."""

import argparse
import logging
import os
import socket
import sys
from datetime import datetime


class Command(object):

    def __init__(self, mpf_path, machine_path, args):

        # Need to have these in here because we don't want them to load when
        # the module is loaded as an mpf.command

        from kivy.logger import Logger
        import mpfmc
        from mpf.core.utility_functions import Util
        from mpfmc.core.config_processor import ConfigProcessor
        from mpfmc.core.mc import MpfMc
        from mpfmc.core.utils import set_machine_path, load_machine_config


        del mpf_path
        parser = argparse.ArgumentParser(description='Starts the MPF Media Controller')

        parser.add_argument("-l",
                            action="store", dest="logfile",
                            metavar='file_name',
                            default=os.path.join("logs", datetime.now().strftime(
                                "%Y-%m-%d-%H-%M-%S-mc-" + socket.gethostname() +
                                ".log")),
                            help="The name (and path) of the log file")

        parser.add_argument("-c",
                            action="store", dest="configfile",
                            default="config", metavar='config_file(s)',
                            help="The name of a config file to load. Default is "
                                 "config.yaml. Multiple files can be used via a comma-"
                                 "separated list (no spaces between)")

        parser.add_argument("-v",
                            action="store_const", dest="loglevel", const=logging.DEBUG,
                            default=logging.INFO, help="Enables verbose logging to the"
                                                       " log file")

        parser.add_argument("-V",
                            action="store_true", dest="consoleloglevel",
                            default=logging.INFO,
                            help="Enables verbose logging to the console. Do NOT on "
                                 "Windows platforms")

        parser.add_argument("-C",
                            action="store", dest="mcconfigfile",
                            default="mcconfig.yaml",
                            metavar='config_file',
                            help="The MPF framework default config file. Default is "
                                 "mc/mcconfig.yaml")

        parser.add_argument("-b",
                            action="store_false", dest="bcp", default=True,
                            help="Do not set up the BCP server threads")

        parser.add_argument("-p",
                            action="store_true", dest="pause", default=True,
                            help="Pause the terminal window on exit. Useful "
                            "when launching in a separate window so you can "
                            "see any errors before the window closes.")

        # The following are just included for full compatibility with mpf.py which is
        # needed when launching from a batch file or shell script.
        parser.add_argument("-x",
                            action="store_const", dest="force_platform",
                            const='virtual', help=argparse.SUPPRESS)

        parser.add_argument("-X",
                            action="store_const", dest="force_platform",
                            const='smart_virtual', help=argparse.SUPPRESS)

        args = parser.parse_args(args)
        args.configfile = Util.string_to_list(args.configfile)

        # Configure logging. Creates a logfile and logs to the console.
        # Formatting options are documented here:
        # https://docs.python.org/2.7/library/logging.html#logrecord-attributes

        # try:
        #     os.makedirs('logs')
        # except OSError as exception:
        #     if exception.errno != errno.EEXIST:
        #         raise
        #
        # logging.basicConfig(level=args.loglevel,
        #                     format='%(asctime)s : %(levelname)s : %(name)s : %(
        # message)s',
        #                     filename=os.path.join(machine_path, args.logfile),
        #                     filemode='w')
        #
        # # define a Handler which writes INFO messages or higher to the sys.stderr
        # console = logging.StreamHandler()
        # console.setLevel(args.consoleloglevel)
        #
        # # set a format which is simpler for console use
        # formatter = logging.Formatter('%(levelname)s : %(name)s : %(message)s')
        #
        # # tell the handler to use this format
        # console.setFormatter(formatter)
        #
        # # add the handler to the root logger
        # logging.getLogger('').addHandler(console)

        mpf_config = ConfigProcessor.load_config_file(os.path.join(
            mpfmc.__path__[0], args.mcconfigfile))

        machine_path = set_machine_path(machine_path,
                                        mpf_config['mpf-mc']['paths'][
                                            'machine_files'])

        mpf_config = load_machine_config(args.configfile, machine_path,
                                         mpf_config['mpf-mc']['paths'][
                                             'config'], mpf_config)

        self.preprocess_config(mpf_config)

        try:
            MpfMc(options=vars(args), config=mpf_config,
                  machine_path=machine_path).run()
            Logger.info("MC run loop ended.")
        except Exception as e:
            # Todo need to change back to a normal exception
            logging.exception(str(e))

        if args.pause:
            input('Press ENTER to close this window...')
        sys.exit()

    def preprocess_config(self, config):

        from kivy.config import Config

        kivy_config = config['kivy_config']

        try:
            kivy_config['graphics'].update(config['window'])
        except KeyError:
            pass

        if ('top' in kivy_config['graphics'] and
                'left' in kivy_config['graphics']):
            kivy_config['graphics']['position'] = 'custom'

        for section, settings in kivy_config.items():
            for k, v in settings.items():
                try:
                    if k in Config[section]:
                        Config.set(section, k, v)
                except KeyError:
                    continue

        if config['window']['exit_on_escape']:
            Config.set('kivy', 'exit_on_escape', '1')

def get_command():
    return 'mc', Command