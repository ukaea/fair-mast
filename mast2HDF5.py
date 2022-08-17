import datetime
from itertools import groupby
import logging
from operator import attrgetter
import os
import random
import time
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import Manager

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
    client = pyuda.Client()
    client.set_property("get_meta", True)
    return client


def update_progress(progress_dict):
    done = progress_dict["progress"] + 1
    total = progress_dict["total"]
    return {"progress": done, "total": total}


class DataRetriever:
    SEGFAULT_SIGNALS = [
        (13174, "ATM_SPECTRA"),
        (14190, "ATM_NELINT"),
        (15549, "ATM_ANE_NELINT"),
        (15583, "ATM_ANE_NELINT"),
    ]

    def __init__(self, logger, client, shot):
        self.logger = logger
        self.client = client
        self.shot = shot

    def retrieve_cpf(self):
        cpf = {}
        for field in pycpf.columns():
            name = field[0]
            entry = pycpf.query(name, f"shot = {self.shot}")
            if entry:
                cpf[name] = {
                    "data": entry[name][0],
                    "description": field[1],
                }
            else:
                cpf[name] = {
                    "data": None,
                    "description": field[1],
                }
        return cpf

    def retrieve_signals(self):
        try:
            signals = self.client.list(ListType.SIGNALS, self.shot)
        except Exception as exception:
            self.logger.error(exception)
            signals = []
        return signals

    def retrieve_source_aliases(self):
        return set([signal.source_alias for signal in self.retrieve_signals()])

    def retrieve_sources(self):
        sources = self.client.list(ListType.SOURCES, self.shot)
        aliases = self.retrieve_source_aliases()
        sources = [source for source in sources if source.source_alias in aliases]
        sources = self.latest_pass_sources(sources)
        return sources

    def latest_pass_sources(self, sources):
        latest_pass_sources = []
        groups = groupby(sources, lambda source: source.source_alias)
        for _, group in groups:
            latest_pass_sources.append(max(group, key=attrgetter("pass_")))
        return latest_pass_sources

    def retrieve_image_sources(self):
        return [
            source
            for source in self.client.list(ListType.SOURCES, self.shot)
            if source.type == "Image"
        ]

    def build_signal_dict(self):
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

    def retrieve_image_data(self, image_data_name):
        try:
            image_data = self.client.get_images(image_data_name, self.shot)
        except Exception as exception:
            self.logger.error(f"{image_data_name}: {exception}")
            image_data = None
        return image_data

    def remove_exceptions(self, signal_name, signal):
        signal_attributes = dir(signal)
        for attribute in signal_attributes:
            try:
                getattr(signal, attribute)
            except Exception as exception:
                self.logger.error(f"{signal_name} {attribute}: {exception}")
                signal_attributes.remove(attribute)
        return signal_attributes

    def retrieve_signal_metadata_fields(self, signal_name):
        signal = self.retrieve_signal(signal_name)
        return [
            attribute
            for attribute in self.remove_exceptions(signal_name, signal)
            if not attribute.startswith("_")
            and attribute not in ["data", "errors", "time"]
            and not callable(getattr(signal, attribute))
        ]

    def retrieve_image_metadata_fields(self, image_source_name):
        image_data = self.retrieve_image_data(image_source_name)
        return [
            field
            for field in dir(image_data)
            if not field.startswith("_")
            and not callable(getattr(image_data, field))
            and field not in ["frames", "frame_times"]
        ]


class Writer:
    def __init__(self, file, logger):
        self.file = file
        self.logger = logger

    def write_cpf(self, cpf):
        self.file.create_group("cpf")
        for key, value in cpf.items():
            try:
                cpf_data = cpf.create_dataset(
                    key,
                    data=value["data"],
                )
                cpf_data.attrs["description"] = value["description"]
            except Exception as exception:
                self.logger.error(f"{key}: {exception}")
                continue

    def write_source_group(self, sources):
        for source in sources:
            group = self.file.create_group(source.source_alias)
            group.attrs["description"] = source.description
            group.attrs["pass"] = source.pass_
            group.attrs["run_id"] = source.run_id
            group.attrs["shot"] = source.shot
            group.attrs["status"] = source.status
            group.attrs["signal_type"] = source.type

    def write_signal(self, source_alias, signal_name, signal, metadata_fields):
        if type(signal) == pyuda._signal.Signal:
            group = self.file.require_group(f"{source_alias}/{signal_name}")
            for field in metadata_fields:
                try:
                    group.attrs[field] = getattr(signal, field)
                except Exception as exception:
                    self.logger.error(f"{signal_name} {field}: {exception}")
            group.create_dataset("data", data=signal.data)
            group.create_dataset("errors", data=signal.errors)
            if signal.time:
                time = group.create_dataset("time", data=signal.time.data)
                time.attrs["units"] = signal.time.units

    def write_image_data(self, source_alias, image_data, image_metadata_fields):
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


def write_file(shot: int, progress, task_id):
    path = "/scratch/ncumming/test"
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
        progress[task_id] = update_progress(progress[task_id])

        if sources:
            writer.write_source_group(sources)
        for source_alias, signal_list in source_dict.items():
            for signal_name in signal_list:
                writer.write_signal(
                    source_alias,
                    signal_name,
                    retriever.retrieve_signal(signal_name),
                    retriever.retrieve_signal_metadata_fields(signal_name),
                )
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


def update_tasks():
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
    overall_progress.start_task(overall_progress_task)
    overall_progress.update(
        overall_progress_task,
        completed=sum([task["progress"] for task in _progress.values()]),
        total=sum([task["total"] for task in _progress.values()]),
    )


def create_progress_table(overall_progress, shot_progress):
    progress_table = Table.grid()
    progress_table.add_row(overall_progress)
    progress_table.add_row()
    progress_table.add_row(Align(shot_progress, align="center"))
    return progress_table


if __name__ == "__main__":
    start_time = time.time()
    first_shot = 8000
    last_shot = 30471
    max_processes = 15
    shots = 15

    if shots == 1:
        shot = 21106
        first_shot = shot
        last_shot = shot

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
                for shot in random.sample(range(first_shot, last_shot + 1), shots):
                    task_id = shot_progress.add_task(f"Shot {shot}", start=False)
                    futures.append(
                        executor.submit(write_file, shot, _progress, task_id)
                    )

                while any([future.running() for future in futures]):
                    finished_processes = sum([future.done() for future in futures])
                    update_tasks()
                    if all([task["total"] for task in _progress.values()]) and any(
                        [task["progress"] for task in _progress.values()]
                    ):
                        update_overall()

            for future in futures:
                future.result()

    execution_time = time.time() - start_time
    with open("times.txt", "a") as file:
        file.write(f"{max_processes},{datetime.timedelta(seconds=execution_time)}\n")
