import xarray as xr
import numpy as np
import pyuda
import os
import logging

logging.basicConfig(
    filename="warning.log",
    filemode="w",
    format="%(name)s - %(levelname)s - %(message)s",
)

client = pyuda.Client()


def main(file_path):
    """Main function for organising function inputs and outputs

    :return: None
    """

    pcs_words_list = []

    setup_dict = {"Shot Number": 0, "Categories": {}}
    cat_list = []

    current_cat = None

    decode_method = "latin_1"

    read_state = 0
    times_found = 0
    vert_found = 0
    array_len = 0
    discard = 0

    """
    Defining the read states, I'm going to write this like a state machine
    state value | state name
    -----------------------------
    0           | idle state where we look for key words
    1           | category key word found so setting recording the category name
    2           | SET_VERTICES key word found so looking for which category to set vertices for
    3           | Getting the phase to set the vertices in
    4           | Getting the waveform to set the vertices in
    5           | Maintain state until a closing bracket is found
    6           | Identified phase timings and maintaing state until timeings found
    """

    with open(file_path, "rb") as setup_read:
        byte = setup_read.read(1)
        pcs_str = byte.decode(decode_method)
        while byte:
            # Read and decode the byte, if the ascii value is not an
            # alphanumeric character then discard it
            byte = setup_read.read(1)
            byte_str = byte.decode(decode_method)

            if len(byte_str) < 1:
                break

            if ord(byte_str) < 32:
                continue

            if ord(byte_str) > 126:
                continue

            # We now do byte sorting to separate into words
            if (
                # byte_str == " "
                byte_str == "\n"
                or byte_str == ","
                or byte_str == "'"
            ):

                # takes the valus in pcs_str and assumes it's a full word
                pcs_str = pcs_str.replace(" ", "")
                pcs_words_list.append(pcs_str)

                # THIS IS THE STATE MACHINE
                if read_state == 0:
                    if pcs_str.find("category") >= 0:
                        read_state = 1
                        # Found the category indicator
                    elif pcs_str.find("SET_VERTICES") >= 0:
                        read_state = 2
                        # Found the set vertices keyword
                    elif pcs_str.find("setuparchivedforshot") >= 0:
                        shot_num_loc = pcs_str.find("setuparchivedforshot")
                        setup_shot_number = float_convert(
                            pcs_str[shot_num_loc + 20 : shot_num_loc + 25]
                        )
                        # if setup_shot_number > setup_dict["Shot Number"]:
                        setup_dict["Shot Number"] = setup_shot_number
                        # print("Found shot number: ", setup_shot_number)

                elif read_state == 1:
                    # print("In state 1 ", pcs_words_list[-10::])
                    # Recording a category name
                    current_cat = pcs_str

                    if not (pcs_str in cat_list):
                        cat_list.append(pcs_str)
                        setup_dict["Categories"][pcs_str] = {}

                        # print("Found category ", current_cat)

                    read_state = 0

                elif read_state == 2:
                    # print("In state 2 ", pcs_words_list[-10::])
                    # Getting the category to set the vertices in
                    current_cat = pcs_str
                    if not (pcs_str in cat_list):
                        cat_list.append(pcs_str)
                        if not (pcs_str in setup_dict["Categories"].keys()):
                            setup_dict["Categories"][pcs_str] = {}

                            # print("Found category ", current_cat)

                    read_state = 3

                elif read_state == 3:
                    # print("In state 3 ", pcs_words_list[-10::])
                    #  Getting the phase to set the vertices in within a category
                    phase_name = pcs_str
                    if not (pcs_str in setup_dict["Categories"][current_cat].keys()):
                        setup_dict["Categories"][current_cat][phase_name] = {
                            "enabled": []
                        }

                        # print("Found phase ", phase_name, " in category ", current_cat)

                    # print("previous bytes discarded: ", str(discard))
                    if discard == 6:
                        read_state = 6
                    else:
                        read_state = 4

                elif read_state == 4:
                    # print("In state 4 ", pcs_words_list[-10::])
                    # Getting the waveform to set the vertices in
                    wave_form = pcs_str
                    if not (
                        pcs_str
                        in setup_dict["Categories"][current_cat][phase_name].keys()
                    ):
                        setup_dict["Categories"][current_cat][phase_name][wave_form] = {
                            "data": [],
                            "time": [],
                        }

                        # print("Found waveform ", wave_form,
                        #       " in phase ", phase_name,
                        #       " of category ", current_cat)

                    read_state = 5

                elif read_state == 5:
                    # print("In state 5 ", array_len, pcs_words_list[-10::])
                    # maintianing this state until time and data has been set
                    if times_found == 0:
                        if pcs_str.find("]") == -1:
                            # if array_len == 0:
                            #     time_array = [float(pcs_str[1:-1])]
                            # else:
                            #     array_len += 1
                            array_len += 1
                            # times_found = 1
                        else:
                            # print("In state 5 setting time ", array_len, pcs_words_list[-10::])
                            array_len += 1
                            time_array = np.zeros(array_len)
                            for i in range(array_len):
                                idx = -1 * (array_len - i)

                                if array_len == 1:
                                    try:
                                        time_array[i] = float_convert(
                                            pcs_words_list[idx][1:-1]
                                        )
                                    except ValueError:
                                        time_array = []
                                elif i == 0:
                                    time_array[i] = float_convert(
                                        pcs_words_list[idx][1::]
                                    )
                                elif idx == -1:
                                    time_array[i] = float_convert(
                                        pcs_words_list[idx][0:-1]
                                    )
                                else:
                                    time_array[i] = float_convert(pcs_words_list[idx])

                            times_found = 1
                            array_len = 0

                    elif times_found == 1:
                        if pcs_str.find("]") == -1:
                            array_len += 1
                        else:
                            if len(time_array) < 1:
                                vert_array = []
                            else:
                                # print("In state 5 setting data", array_len, pcs_words_list[-10::])
                                array_len += 1
                                vert_array = np.zeros(array_len)
                                for i in range(array_len):
                                    idx = -1 * (array_len - i)

                                    # print(pcs_words_list[idx::])
                                    vert_array[i] = convertVertString(
                                        pcs_words_list[idx]
                                    )

                            vert_found = 1
                            array_len = 0

                    if times_found == 1 and vert_found == 1:

                        setup_dict["Categories"][current_cat][phase_name][wave_form][
                            "data"
                        ] = vert_array
                        setup_dict["Categories"][current_cat][phase_name][wave_form][
                            "time"
                        ] = time_array

                        # print(
                        #     "\nSet data for category ",
                        #     current_cat,
                        #     " using phase ",
                        #     phase_name,
                        #     ":",
                        # )
                        # print(wave_form, " data:", vert_array)
                        # print(wave_form, " time:", time_array, "\n")
                        read_state = 0
                        times_found = 0
                        vert_found = 0

                elif read_state == 6:
                    # print("In state 6 ", array_len, pcs_words_list[-10::])
                    # Found the phase vertices for a category
                    if times_found == 0:
                        # print(pcs_str)
                        if pcs_str.find("]") == -1:
                            # if array_len == 0:
                            #     time_array = [float(pcs_str[1:-1])]
                            # else:
                            array_len += 1

                            # times_found = 1
                        else:
                            array_len += 1
                            time_array = np.zeros(array_len)
                            for i in range(array_len):
                                idx = -1 * (array_len - i)

                                if array_len == 1:
                                    time_array[i] = float_convert(
                                        pcs_words_list[idx][1:-1]
                                    )
                                elif i == 0:
                                    # print(pcs_words_list[idx], idx, array_len)
                                    time_array[i] = float_convert(
                                        pcs_words_list[idx][1::]
                                    )
                                elif idx == -1:
                                    time_array[i] = float_convert(
                                        pcs_words_list[idx][0:-1]
                                    )
                                else:
                                    time_array[i] = float_convert(pcs_words_list[idx])

                            times_found = 1
                            array_len = 0

                    elif times_found == 1:
                        if pcs_str.find("]") >= 0:
                            # array_len += 1
                            # elif pcs_str.find("[") >= 0:
                            #     pass
                            # else:
                            array_len = len(time_array)
                            vert_array = []
                            for i in range(array_len):
                                idx = -1 * (array_len - i) - 1
                                # print(idx, i)
                                vert_array.append(
                                    convertVertString(pcs_words_list[idx])
                                )

                            vert_found = 1
                            array_len = 0

                    if times_found == 1 and vert_found == 1:

                        for p, phase_name in enumerate(vert_array):
                            if not (
                                pcs_str in setup_dict["Categories"][current_cat].keys()
                            ):
                                setup_dict["Categories"][current_cat][phase_name] = {
                                    "enabled": []
                                }

                            setup_dict["Categories"][current_cat][phase_name][
                                "enabled"
                            ].append(time_array[p])

                        # print("Phases found in category ", current_cat, ": ", vert_array)
                        # print("Phase changes at: ", time_array, "\n")
                        read_state = 0
                        times_found = 0
                        vert_found = 0

                discard = 0
                while (
                    # byte_str == " "
                    byte_str == "\n"
                    or byte_str == ","
                    or byte_str == "'"
                ):

                    byte = setup_read.read(1)
                    byte_str = byte.decode(decode_method)
                    discard += 1
                # print("bytes thrown away:", str(discard))

                pcs_str = byte_str

            else:
                pcs_str += byte_str

    return setup_dict


def float_convert(target):
    if target.endswith("..."):
        new_value = target.rstrip("...")
        return float(new_value)
    else:
        return float(target)


def convertVertString(sn_string):
    # Function to convert a vertice value in bytes into a
    # usable value for the setup dictionary

    if sn_string.find("[") >= 0:
        sn_string = sn_string[1::]

    if sn_string.find("]") >= 0:
        sn_string = sn_string[0:-1]

    if sn_string.find("e") >= 0:
        sn_vals = sn_string.split("e")
        try:
            vert_val = float_convert(sn_vals[0]) * (10 ** float_convert(sn_vals[1]))
        except ValueError:
            vert_val = str(sn_string)
    else:
        try:
            vert_val = float_convert(sn_string)
        except ValueError:
            # print(sn_string)
            vert_val = str(sn_string)

    return vert_val


def read_pcs_data(shot: int) -> xr.Dataset:
    """Runs the main conversion for the shot inputted, retrieving the PCS data.
    Has logging included for any server exceptions and/or valueErrors.

    Args:
        shot (int): Shot number to retrieve PCS data from.

    Returns:
        dict: Dictionary containing all of the data for PCS for the shot.
    """
    dirname = "./"

    tag = "pcs"

    if tag == "pcs":
        shotfile = f"pcs{shot//100:04d}.{shot%100:02d}"
    else:
        shotfile = f"{tag}{shot:06d}.nc"

    print(f"fetching file {shotfile}")
    fetchpath = f"$MAST_DATA/{shot//1000:03d}/{shot}/LATEST/{shotfile}"
    targetpath = f"{dirname}/{shotfile}"
    print(f"{fetchpath} ==> {targetpath}")
    try:
        client.get_file(fetchpath, targetpath)
        setup_dict = main(targetpath)
        setup_dict["Shot Number"] = shot
        os.remove(shotfile)
        dataset = convert_to_dataset(setup_dict)
        return dataset
    except pyuda.ServerException:
        logging.error(f"{shot} not found on server.")
        return None
    except ValueError:
        logging.exception(f"{shot} has ValueError")
        os.remove(shotfile)
        return None


def convert_to_dataset(data: dict) -> xr.Dataset:
    names = set()

    result_datasets = {}
    for name, category in data["Categories"].items():
        for _, item in category.items():
            for key, variable in item.items():
                if key == "enabled":
                    continue

                label = f"{name}_{key}".upper()
                if label in names:
                    continue

                names.add(label)
                dataset = xr.Dataset(
                    dict(
                        data=xr.DataArray(variable["data"], dims=["time"]),
                        time=xr.DataArray(variable["time"], dims=["time"]),
                    ),
                    attrs=dict(name=f"PCS_{label}"),
                )

                result_datasets[label] = dataset

    return result_datasets
