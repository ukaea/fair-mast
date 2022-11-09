"""This script converts MAST shot data into a single HDF5 file for each shot"""
import datetime
import logging
import os
import random
import time
import argparse
import getpass
from concurrent.futures import ProcessPoolExecutor
from distutils.dir_util import copy_tree
from itertools import groupby
from multiprocessing import Manager
from operator import attrgetter

import h5py
import numpy as np
import pyuda
from mast.mast_client import ListType
from pycpf import pycpf
from rich.align import Align
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn
from rich.table import Table


def set_client():
    """Instatiates a UDA Client and sets it to also retrieve metadata"""
    client = pyuda.Client()
    client.set_property("get_meta", True)
    return client


def update_progress(progress_dict):
    """Updates the dictionary containing the progress information for each process"""
    done = progress_dict["progress"] + 1
    total = progress_dict["total"]
    return {"progress": done, "total": total}


def update_tasks():
    """Updates the tasks in the progress bar.

    _progess is a managed dictionary that collects progress information from each of
    the processes. This function uses that information to update the progress bar.
    """
    for task_id, update_data in _progress.items():
        latest = update_data["progress"]
        total = update_data["total"]
        if latest:
            shot_progress.start_task(task_id)
        shot_progress.update(
            task_id,
            completed=latest,
            total=total,
        )


def update_overall():
    """Updates the "overall progress" bar"""
    overall_progress.start_task(overall_progress_task)
    overall_progress.update(
        overall_progress_task,
        completed=sum([task["progress"] for task in _progress.values()]),
        total=sum([task["total"] for task in _progress.values()]),
    )


def create_progress_table(overall_progress, shot_progress):
    """Creates the table to contain the progress information"""
    progress_table = Table.grid()
    progress_table.add_row(overall_progress)
    progress_table.add_row()
    progress_table.add_row(Align(shot_progress, align="center"))
    return progress_table


def choose_random_shots(first_shot, last_shot, shots):
    """Produces a random selection of shots between first_shot and last_shot"""
    return random.sample(range(first_shot, last_shot + 1), shots)

def get_args():
    """Gets the arguments for output path and shots to process from the user"""
    parser = argparse.ArgumentParser()
    username = getpass.getuser()
    parser.add_argument(
        "-o",
        "--output_path",
        type=str,
        default=f"/tmp/{username}/mast2HDF5",
        help="Enter output path for .h5 files, default is /tmp/$USERNAME/mast2HDF5",
    )
    parser.add_argument(
        "-s",
        "--shots",
        type=int,
        required=True,
        nargs="+",
        help="Enter shot names to process. Shot names only between 8000 t0 30471",
    )
    shots = parser.parse_args().shots
    path = parser.parse_args().output_path
    return shots, path


def move_to_stage():
    """A slow function that should be removed"""
    write_directory = "/scratch/ncumming/write"
    stage_directory = "/scratch/ncumming/stage"
    copy_tree(write_directory, stage_directory)


def write_file(shot: int, batch_size: int, progress, task_id):
    """The main function that retrieves the shot data, and writes it to HDF5

    Parameters
    ----------
    shot : int
        shot number
    batch_size : int
        number of signals that are requested from UDA server in each call to
        client.get_batch()
    progress : dict
        dictionary containing progress information
    task_id : int
        used by the progress bar to identify each parallel process
    """
    logfiles_path = os.path.join(path, "logs")
    os.makedirs(logfiles_path, exist_ok=True)
    logging.basicConfig(
        filename=os.path.join(logfiles_path, f"{shot}.log"),
        format="%(asctime)s | %(levelname)s | %(message)s",
    )
    logger = logging.getLogger(f"{shot}_log")
    file_path = os.path.join(path, f"{shot}.h5")
    retriever = DataRetriever(logger, set_client(), shot)
    sources = retriever.retrieve_sources()
    image_sources = retriever.retrieve_image_sources()
    source_dict = retriever.build_signal_dict()
    sources_total = len(source_dict) + len(image_sources) + 1
    tasks_completed = 0
    progress[task_id] = {"progress": tasks_completed, "total": sources_total}

    with h5py.File(file_path, "a") as file:
        writer = Writer(file, logger)
        cpf = retriever.retrieve_cpf()
        writer.write_cpf(cpf)
        writer.write_definitions(cpf)
        progress[task_id] = update_progress(progress[task_id])

        if sources:
            writer.write_source_group(sources)
        for source_alias, signal_list in source_dict.items():
            signal_dict = {}
            batches = [
                list(signal_list)[i : i + batch_size]
                for i in range(0, len(signal_list), batch_size)
            ]
            for batch in batches:
                signal_batch = retriever.retrieve_signal_batch(batch)
                batch_dict = dict(zip(batch, signal_batch))
                signal_dict.update(batch_dict)

            for signal_name in signal_list:
                logger.error("Starting %s", signal_name)
                signal_object = signal_dict[signal_name]
                writer.write_signal(
                    source_alias,
                    signal_name,
                    signal_object,
                    retriever.retrieve_signal_metadata_fields(
                        signal_object, signal_name
                    ),
                )
                logger.error("Done %s", signal_name)
            progress[task_id] = update_progress(progress[task_id])

        if image_sources:
            for image_source in image_sources:
                if (image_source.format == "TIF") or (
                    image_source.source_alias == "rcc"
                ):
                    progress[task_id] = update_progress(progress[task_id])
                    continue
                image_data = retriever.retrieve_image_data(image_source.source_alias)
                image_metadata_fields = retriever.retrieve_image_metadata_fields(
                    image_source.source_alias
                )
                if image_data:
                    writer.write_image_data(
                        image_source.source_alias, image_data, image_metadata_fields
                    )
                progress[task_id] = update_progress(progress[task_id])


class DataRetriever:
    """
    Handles the retrieval of data via UDA and pycpf

    This class uses it's own UDA client to determine the sources and signals available for a given
    shot, and retrieves those signals. It also handles retrieval of the cpf data.

    Attributes
    ----------
    SEGFAULT_SIGNALS : list
                       A list of signals for some given shot that are known to cause segfaults upon
                       retrieval. These signals are skipped.
    """

    SEGFAULT_SIGNALS = [
        (13174, "ATM_SPECTRA"),
        (14190, "ATM_NELINT"),
        (14915, "ATM_NELINT"),
        (15549, "ATM_ANE_NELINT"),
        (15583, "ATM_ANE_NELINT"),
    ]

    def __init__(self, logger, client, shot):
        """Instantiates the class with a logger, a UDA client, and a shot number"""
        self.logger = logger
        self.client = client
        self.shot = shot

    def retrieve_cpf(self):
        """Retrieves the cpf data and returns it as a dictionary

        The cpf (central physics file) contains a summary of the shot in the form of plasma
        classifiers and parameters. The returned dictionary contains both a value and description
        for each cpf entry.
        """
        cpf = {}
        for field in pycpf.columns():
            name = field[0]
            entry = pycpf.query(name, f"shot = {self.shot}")
            if entry:
                cpf[name] = {
                    "value": entry[name][0],
                    "description": field[1],
                }
            else:
                cpf[name] = {
                    "value": None,
                    "description": field[1],
                }
        return cpf

    def retrieve_signals(self):
        """Returns a list of all the signals available via UDA for that shot"""
        try:
            signals = self.client.list(ListType.SIGNALS, self.shot)
        except Exception as exception:
            self.logger.error(exception)
            signals = []
        return signals

    def retrieve_source_aliases(self):
        """Returns a list of all unique sources of the available signals"""
        return set(signal.source_alias for signal in self.retrieve_signals())

    def retrieve_sources(self):
        """Retruns a list of all of the sources for that shot

        Only the sources of the available signals are returned, to prevent the retrieval of sources
        that may not contain any actual signals.
        """
        sources = self.client.list(ListType.SOURCES, self.shot)
        aliases = self.retrieve_source_aliases()
        sources = [source for source in sources if source.source_alias in aliases]
        sources = self.latest_pass_sources(sources)
        return sources

    def latest_pass_sources(self, sources):
        """Returns all the sources written by the latest pass of the data"""
        latest_pass_sources = []
        groups = groupby(sources, lambda source: source.source_alias)
        for _, group in groups:
            latest_pass_sources.append(max(group, key=attrgetter("pass_")))
        return latest_pass_sources

    def retrieve_image_sources(self):
        """Retrieves all sources that a classified as "Image" data"""
        return [
            source
            for source in self.client.list(ListType.SOURCES, self.shot)
            if source.type == "Image"
        ]

    def build_signal_dict(self):
        """Returns a dictionary of all the sources for the shot with the full list of signals for
        each
        """
        aliases = self.retrieve_source_aliases()
        return {
            source: set(
                [
                    signal.signal_name
                    for signal in self.retrieve_signals()
                    if signal.source_alias == source
                ]
            )
            for source in aliases
        }

    def retrieve_signal(self, signal_name):
        """Retrieves the signal object via the UDA client"""
        if (self.shot, signal_name) in DataRetriever.SEGFAULT_SIGNALS:
            self.logger.error(
                f"{signal_name}: This signal has been found to cause a Segfault, skipping."
            )
            return None
        try:
            signal = self.client.get(signal_name, self.shot)
        except Exception as exception:
            self.logger.error(f"{signal_name}: {exception}")
            signal = None
        return signal

    def retrieve_signal_batch(self, signal_names):
        """Retrieves a list of signals via the UDA client using the client.get_batch() API

        If this fails, it falls back to the normal client.get() method.
        """
        for signal_name in signal_names:
            if (self.shot, signal_name) in DataRetriever.SEGFAULT_SIGNALS:
                self.logger.error(
                    f"{signal_name}: This signal has been found to cause a Segfault, skipping."
                )
                signal_names.remove(signal_name)
        try:
            signals = self.client.get_batch(signal_names, self.shot)
        except Exception as exception:
            self.logger.error(
                f"Dropped batch {signal_names}: {exception} \n Falling back to series retrieval"
            )
            signals = []
            for signal_name in signal_names:
                signals.append(self.retrieve_signal(signal_name))
        return signals

    def retrieve_image_data(self, image_data_name):
        """Retrieves image data for the given image source"""
        try:
            image_data = self.client.get_images(image_data_name, self.shot)
        except Exception as exception:
            self.logger.error(f"{image_data_name}: {exception}")
            image_data = None
        return image_data

    def remove_exceptions(self, signal_name, signal):
        """Handles when signal attributes contain exception objects"""
        signal_attributes = dir(signal)
        for attribute in signal_attributes:
            try:
                getattr(signal, attribute)
            except Exception as exception:
                self.logger.error(f"{signal_name} {attribute}: {exception}")
                signal_attributes.remove(attribute)
        return signal_attributes

    def retrieve_signal_metadata_fields(self, signal, signal_name):
        """Retrieves the appropriate metadata field for a given signal"""
        return [
            attribute
            for attribute in self.remove_exceptions(signal_name, signal)
            if not attribute.startswith("_")
            and attribute not in ["data", "errors", "time", "meta", "dims"]
            and not callable(getattr(signal, attribute))
        ]

    def retrieve_image_metadata_fields(self, image_source_name):
        """Retrieves the appropriate metadata field for a given image source"""
        image_data = self.retrieve_image_data(image_source_name)
        return [
            field
            for field in dir(image_data)
            if not field.startswith("_")
            and not callable(getattr(image_data, field))
            and field not in ["frames", "frame_times"]
        ]


class Writer:
    """Handles writing the data to an HDF5 file."""

    def __init__(self, file, logger):
        """Instantiates the class with an HDF5 file and logger"""
        self.file = file
        self.logger = logger

    def write_cpf(self, cpf):
        """Writes the cpf as top-level metadata"""
        for name, entry in cpf.items():
            try:
                self.file.attrs[name] = entry["value"]
            except Exception as exception:
                self.logger.error(f"{name}: {exception}")
                continue

    def write_definitions(self, cpf):
        """Creates a definitions groups containing cpf names along with their descriptions"""
        group = self.file.create_group("definitions")
        for key, value in cpf.items():
            try:
                group.attrs[key] = value["description"]
            except Exception as exception:
                self.logger.error(f"{key}: {exception}")
                continue

    def write_source_group(self, sources):
        """Creates a group at the top level of the HDF5 file for each source and fills its
        metadata
        """
        for source in sources:
            group = self.file.create_group(source.source_alias)
            group.attrs["description"] = source.description
            group.attrs["pass"] = source.pass_
            group.attrs["run_id"] = source.run_id
            group.attrs["shot"] = source.shot
            group.attrs["status"] = source.status
            group.attrs["signal_type"] = source.type

    def write_signal(self, source_alias, signal_name, signal, metadata_fields):
        """Writes the signal data"""
        if isinstance(signal, pyuda._signal.Signal) and signal.data is not None:
            group = self.file.require_group(f"{source_alias}/{signal_name}")
            for field in metadata_fields:
                try:
                    group.attrs[field] = getattr(signal, field)
                except Exception as exception:
                    self.logger.error(f"{signal_name} {field}: {exception}")
            if signal.meta:
                group.attrs["pass_date"] = signal.meta["pass_date"].decode()
            group.create_dataset("data", data=signal.data)
            group.create_dataset("errors", data=signal.errors)
            if signal.time:
                time = group.create_dataset("time", data=signal.time.data)
                time.attrs["units"] = signal.time.units
        else:
            self.logger.error(f"{signal_name}: Is not a signal or was empty object")

    def write_image_data(self, source_alias, image_data, image_metadata_fields):
        """Writes the image data for a given image source"""
        group = self.file.require_group(source_alias)
        for field in image_metadata_fields:
            group.attrs[field] = getattr(image_data, field)

        try:
            group.create_dataset("frame_times", data=image_data.frame_times)
        except Exception as exception:
            self.logger.error(f"{source_alias}: {exception}")
        if image_data.is_color:
            for frame in image_data.frames:
                combined_rgb = np.dstack((frame.r, frame.g, frame.b))
                data = group.create_dataset(str(frame.number), data=combined_rgb)
                data.attrs["IMAGE_SUBCLASS"] = np.string_("IMAGE_TRUECOLOR")
                data.attrs["INTERLACE_MODE"] = np.string_("INTERLACE_PIXEL")
                data.attrs["time"] = frame.time
                data.attrs["CLASS"] = np.string_("IMAGE")
                data.attrs["IMAGE_VERSION"] = np.string_("1.2")
        else:
            for frame in image_data.frames:
                data = group.create_dataset(str(frame.number), data=frame.k)
                data.attrs["IMAGE_SUBCLASS"] = np.string_("IMAGE_INDEXED")
                data.attrs["time"] = frame.time
                data.attrs["CLASS"] = np.string_("IMAGE")
                data.attrs["IMAGE_VERSION"] = np.string_("1.2")


if __name__ == "__main__":
    shots = get_args()[0]
    path = get_args()[1]
    start_time = time.time()
    first_shot = 8000
    last_shot = 30471
    max_processes = 5  # Any more than this will be more than a Freia node can handle
    batch_size = 10

    overall_progress = Progress(
        SpinnerColumn(),
        *Progress.get_default_columns(),
        TimeElapsedColumn(),
    )
    shot_progress = Progress()
    progress_table = create_progress_table(overall_progress, shot_progress)

    with Live(Panel.fit(progress_table, title="Converting MAST data to HDF5")):
        futures = []
        with Manager() as manager:
            _progress = manager.dict()
            overall_progress_task = overall_progress.add_task(
                "[green]Total progress:", start=False
            )

            with ProcessPoolExecutor(max_workers=max_processes) as executor:
                for shot in shots:
                    task_id = shot_progress.add_task(f"Shot {shot}", start=False)
                    futures.append(
                        executor.submit(
                            write_file, shot, batch_size, _progress, task_id
                        )
                    )

                while any(future.running() for future in futures):
                    finished_processes = sum([future.done() for future in futures])
                    update_tasks()
                    if all(task["total"] for task in _progress.values()) and any(
                        task["progress"] for task in _progress.values()
                    ):
                        update_overall()

            for future in futures:
                future.result()

    # move_to_stage()

    execution_time = time.time() - start_time
    with open("times.txt", "a", encoding="utf-8") as file:
        file.write(f"{max_processes},{datetime.timedelta(seconds=execution_time)}\n")
