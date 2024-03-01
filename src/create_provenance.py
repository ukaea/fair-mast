import sys
import fusionprov
import json
import pandas as pd
import logging
import traceback
import click
import multiprocessing as mp
from rich.progress import track
from pathlib import Path
from src.uda import UDAClient

def setup_logger():
    logging.basicConfig(level=logging.ERROR)
    logger = logging.getLogger("prov_writer")

    file_handler = logging.FileHandler('prov_log.txt', mode='w')
    logger.addHandler(file_handler)

    return logger


def log_finished_shot(shot_num, path):
    with path.open('a') as handle:
        handle.write(f'{shot_num}\n')


def get_finished_shots(path):
    if not path.exists():
        return []

    with path.open('r') as handle:
        lines = handle.readlines()

    shot_nums = map(int, lines)
    shot_nums = list(shot_nums)
    return shot_nums


class SegFaultHandler:

    def __init__(self, logger):
        self.logger = logger

    def __call__(self, signum, frame):
        self.logger.info("SegFault!")
        self.logger.info(signum, frame)
        self.logger.info(traceback.print_stack(frame))


class ProvenanceWriter:

    def __init__(self, logger):
        self.logger = logger
        self.client = None

    def write_shot_provenance(self, shot: int):
        """Write provenance data for all signals for a shot"""
        self.client = UDAClient(self.logger)
        signals = self.client.list_signals(shot)

        if signals is None:
            self.logger.error(f'{shot}: No signals found!')
            return

        for signal in signals:
            self.write_signal_provenance(shot, signal.signal_name)
        
        return shot

    def write_signal_provenance(self, shot: int , name: str):
        """Write provenance data for a single signal"""

        self.logger.info(f'{shot} - {name}')

        try:
            fusionprov.write_provenance(name, shot, graph=False, json=True, xml=False)
        except Exception as exception:
            self.logger.error(f'{shot}: could not parse prov information for signal {name}. Exception: {exception}')


def do_write_prov(shot: int):
    logger = setup_logger()
    ProvenanceWriter(logger).write_shot_provenance(shot)
    return shot

@click.command()
@click.argument('shot_file')
def main(shot_file):
    import signal
    cache = True

    logger = setup_logger()
    signal.signal(signal.SIGSEGV, SegFaultHandler(logger))

    log_file_name = Path('log.txt')
    finished_shot_nums = get_finished_shots(log_file_name)

    shots = pd.read_csv(shot_file, index_col=None)['shot_id'].values
    shots = list(sorted(shots))

    pool = mp.Pool(16)
    for shot in track(pool.map(do_write_prov, shots), total=len(shots)):
        log_finished_shot(shot, log_file_name)

if __name__ == "__main__":
    main()
