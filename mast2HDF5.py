import datetime
import random
import time
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import Manager

import h5py
import pyuda
from mast.mast_client import ListType
from pycpf import pycpf
from rich.progress import Progress


def write_file(shot, progress):
    client = pyuda.Client()
    client.set_property("get_meta", True)
    file_path = f"/scratch/ncumming/{shot}.h5"
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

    with h5py.File(file_path, "a") as file:
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
                except Exception as e:
                    # TODO: log this
                    continue

        for source in sources:
            group = file.create_group(source.source_alias)
            group.attrs["description"] = source.description
            group.attrs["pass"] = source.pass_
            group.attrs["run_id"] = source.run_id
            group.attrs["shot"] = source.shot
            group.attrs["status"] = source.status
            group.attrs["signal_type"] = source.type

        for source, signal_list in source_dict.items():
            for signal_name in signal_list:
                try:
                    data = client.get(signal_name, shot)
                except Exception as exception:
                    # TODO: log this
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
                    dataset.attrs["units"] = data.units
                    group.create_dataset("errors", data=data.errors)
                    if data.time:
                        time = group.create_dataset("time", data=data.time.data)
                        time.attrs["units"] = data.time.units

        images = file.create_group("images")
        for image_source in image_sources:
            if (image_source.format == "TIF") or (image_source.source_alias == "rcc"):
                continue
            image_data = client.get_images(image_source.source_alias, shot)
            image_group = images.create_group(image_source.source_alias)
            attributes = {
                "board_temp": image_data.board_temp,
                "bottom": image_data.bottom,
                "camera": image_data.camera,
                "ccd_temp": image_data.ccd_temp,
                "codex": image_data.codex,
                "date_time": image_data.date_time,
                "depth": image_data.depth,
                "exposure": image_data.exposure,
                "filter": image_data.filter,
                "gain": image_data.gain,
                "hbin": image_data.hbin,
                "height": image_data.height,
                "is_color": image_data.is_color,
                "left": image_data.left,
                "lens": image_data.lens,
                "n_frames": image_data.n_frames,
                "offset": image_data.offset,
                "orientation": image_data.orientation,
                "pre_exp": image_data.pre_exp,
                "right": image_data.right,
                "shot": image_data.shot,
                "strobe": image_data.strobe,
                "taps": image_data.taps,
                "top": image_data.top,
                "trigger": image_data.trigger,
                "vbin": image_data.vbin,
                "view": image_data.view,
                "width": image_data.width,
            }
            for key, value in attributes.items():
                image_group.attrs[key] = value

            image_group.create_dataset(
                "frame_times",
                data=image_data.frame_times,
            )
            frames_group = image_group.create_group("frames")
            for frame in image_data.frames:
                frame_group = frames_group.create_group(f"frame_{frame.number}")
                keys = dir(frame)
                keys = [key for key in keys if not key.startswith("_")]
                for key in keys:
                    frame_group.create_dataset(key, data=getattr(frame, key))


if __name__ == "__main__":
    start_time = time.time()
    shot_list = [
        29976,
        30420,
        30422,
        30426,
        30430,
        30449,
        30464,
        30468,
        30469,
        30471,
    ]
    processes = 2

    with Progress() as progress:
        futures = []
        with Manager() as manager:
            _progress = manager.dict()
            overall_progress_task = progress.add_task("[green]All jobs progress:")
            with ProcessPoolExecutor(max_workers=processes) as executor:
                for shot in random.sample(shot_list, processes):
                    futures.append(
                        executor.submit(write_file, shot, progress=_progress)
                    )

                finished_processes = sum([future.done() for future in futures])
                while finished_processes < len(futures):
                    progress.update(
                        overall_progress_task,
                        completed=finished_processes,
                        total=len(futures),
                    )
                    for task_id, update_data in _progress.items():
                        latest = update_data["progress"]
                        total = update_data["total"]
                        # update the progress bar for this task:
                        progress.update(
                            task_id,
                            completed=latest,
                            total=total,
                            visible=latest < total,
                        )
                    finished_processes = sum([future.done() for future in futures])

            for future in futures:
                future.result()

        execution_time = time.time() - start_time
        with open("times.txt", "a") as file:
            file.write(f"{processes},{datetime.timedelta(seconds=execution_time)}\n")
