import datetime
import logging
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


def get_sources(client, shot):
    sources = client.list(ListType.SOURCES, shot)
    image_sources = [source for source in sources if source.type == "Image"]
    signals = client.list(ListType.SIGNALS, shot)
    aliases = set([signal.source_alias for signal in signals])
    sources = [source for source in sources if source.source_alias in aliases]
    source_dict = {
        source: set(
            [signal.signal_name for signal in signals if signal.source_alias == source]
        )
        for source in aliases
    }
    return sources, image_sources, source_dict


def write_cpf(file, shot, logger):
    cpf = file.create_group("cpf")
    cpf_categories = pycpf.columns()
    for entry in cpf_categories:
        cpf_entry = pycpf.query(entry[0], f"shot = {shot}")
        if cpf_entry:
            try:
                cpf_data = cpf.create_dataset(
                    entry[0],
                    data=cpf_entry[entry[0]][0],
                )
                cpf_data.attrs["description"] = entry[1]
            except Exception as exception:
                logger.error(f"{entry[0]}: {exception}")
                continue


def create_source_group(file, sources):
    for source in sources:
        group = file.create_group(source.source_alias)
        group.attrs["description"] = source.description
        group.attrs["pass"] = source.pass_
        group.attrs["run_id"] = source.run_id
        group.attrs["shot"] = source.shot
        group.attrs["status"] = source.status
        group.attrs["signal_type"] = source.type


def write_source(file, client, source, signal_list, logger):
    for signal_name in signal_list:
        try:
            data = client.get(signal_name, shot)
        except Exception as exception:
            logger.error(f"{signal_name}: {exception}")
            continue

        if type(data) == pyuda._signal.Signal:
            if signal_name.startswith("/"):
                signal_alias = signal_name[5:]
            else:
                signal_alias = signal_name[4:]

            group = file.create_group(f"{source}/{signal_alias}")
            group.attrs["description"] = data.description
            group.attrs["label"] = data.label
            group.attrs["pass"] = data.meta["pass"]
            group.attrs["pass_date"] = data.meta["pass_date"]
            dataset = group.create_dataset("data", data=data.data)
            try:
                dataset.attrs["units"] = data.units
            except Exception as exception:
                logger.error(f"{signal_name} units: {exception}")
            group.create_dataset("errors", data=data.errors)
            if data.time:
                time = group.create_dataset("time", data=data.time.data)
                time.attrs["units"] = data.time.units


def write_image_source(images_group, client, image_source):
    image_data = client.get_images(image_source.source_alias, shot)
    source_group = images_group.create_group(image_source.source_alias)
    image_attributes = [
        attribute
        for attribute in dir(image_data)
        if not attribute.startswith("_")
        and not callable(getattr(image_data, attribute))
        and attribute not in ["frames", "frame_times"]
    ]
    for attribute in image_attributes:
        source_group.attrs[attribute] = getattr(image_data, attribute)

    source_group.create_dataset("frame_times", data=image_data.frame_times)
    if image_data.is_color:
        for frame in image_data.frames:
            combined_rgb = np.dstack((frame.r, frame.g, frame.b))
            data = source_group.create_dataset(str(frame.number), data=combined_rgb)
            data.attrs["IMAGE_SUBCLASS"] = np.string_("IMAGE_TRUECOLOR")
            data.attrs["INTERLACE_MODE"] = np.string_("INTERLACE_PIXEL")
            data.attrs["time"] = frame.time
            data.attrs["CLASS"] = np.string_("IMAGE")
            data.attrs["IMAGE_VERSION"] = np.string_("1.2")
    else:
        for frame in image_data.frames:
            data = source_group.create_dataset(str(frame.number), data=frame.k)
            data.attrs["IMAGE_SUBCLASS"] = np.string_("IMAGE_INDEXED")
            data.attrs["time"] = frame.time
            data.attrs["CLASS"] = np.string_("IMAGE")
            data.attrs["IMAGE_VERSION"] = np.string_("1.2")


def update_progress(progress_dict, total, done):
    done += 1
    progress_dict = {"progress": done, "total": total}
    return progress_dict, done


def write_file(shot, progress, task_id):
    path = "/scratch/ncumming/test"
    logfiles_path = os.path.join(path, "logs")
    os.makedirs(logfiles_path, exist_ok=True)
    logging.basicConfig(
        filename=os.path.join(logfiles_path, f"{shot}.log"),
        format="%(asctime)s | %(levelname)s | %(message)s",
    )
    logger = logging.getLogger(f"{shot}_log")
    client = set_client()
    file_path = os.path.join(path, f"{shot}.h5")
    try:
        sources, image_sources, source_dict = get_sources(client, shot)
    except Exception as exception:
        logger.error(f"{shot}: {exception}")
        return
    sources_total = len(source_dict) + len(image_sources) + 1
    tasks_completed = 0
    progress[task_id] = {"progress": tasks_completed, "total": sources_total}

    with h5py.File(file_path, "a") as file:
        write_cpf(file, shot, logger)
        progress[task_id], tasks_completed = update_progress(
            progress[task_id], sources_total, tasks_completed
        )
        create_source_group(file, sources)
        for source, signal_list in source_dict.items():
            write_source(file, client, source, signal_list, logger)
            progress[task_id], tasks_completed = update_progress(
                progress[task_id], sources_total, tasks_completed
            )

        image_group = file.create_group("images")
        for image_source in image_sources:
            if (image_source.format == "TIF") or (image_source.source_alias == "rcc"):
                progress[task_id], tasks_completed = update_progress(
                    progress[task_id], sources_total, tasks_completed
                )
                continue
            write_image_source(image_group, client, image_source)
            progress[task_id], tasks_completed = update_progress(
                progress[task_id], sources_total, tasks_completed
            )


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


if __name__ == "__main__":
    start_time = time.time()
    first_shot = 8000
    last_shot = 30471
    processes = 10

    overall_progress = Progress(
        SpinnerColumn(),
        *Progress.get_default_columns(),
        TimeElapsedColumn(),
    )
    shot_progress = Progress()
    progress_table = Table.grid()
    progress_table.add_row(overall_progress)
    progress_table.add_row()
    progress_table.add_row(Align(shot_progress, align="center"))

    with Live(Panel.fit(progress_table, title="Converting MAST data to HDF5")):
        futures = []
        with Manager() as manager:
            _progress = manager.dict()
            overall_progress_task = overall_progress.add_task(
                "[green]Total progress:", start=False
            )

            with ProcessPoolExecutor(max_workers=processes) as executor:
                for shot in random.sample(range(first_shot, last_shot + 1), processes):
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
        file.write(f"{processes},{datetime.timedelta(seconds=execution_time)}\n")
