#!/usr/bin/python

# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------
import csv
import sys
import os
import datetime

from nupic.frameworks.opf.modelfactory import ModelFactory
from nupic.swarming import permutations_runner
from nupic.data.inference_shifter import InferenceShifter


date_format_EU = "%Y-%m-%d"
date_format_US = "%m/%d/%y %H:%M"
date_format = None

input_file_name = ""
predicted_field_name = ""
predicted_field_type = ""
max_value = -1
min_value = 1
predicted_field_row = -1
last_record = -1


stored_input_file = []

SWARM_CONFIG = {
    "includedFields": [
        {
            "fieldName": predicted_field_name,
            "fieldType": predicted_field_type,
            "maxValue": max_value,
            "minValue": min_value
        }
    ],
    "streamDef": {
        "info": predicted_field_name,
        "version": 1,
        "streams": [
            {
                "info": predicted_field_name,
                "source": "file://" + input_file_name,
                "columns": ["*"],
                "last_record": last_record
            }
        ]
    },

    "inferenceType": "TemporalAnomaly",
    "inferenceArgs": {
        "predictionSteps": [
            1
        ],
        "predictedField": predicted_field_name
    },
    "iterationCount": -1,
    "swarmSize": "medium"
}

def configure_swarm_parameters(param_input_file_name, param_last_record, param_date_type, param_included_fields,):
    global input_file_name
    global predicted_field_name
    global predicted_field_row
    global predicted_field_type
    global max_value
    global min_value
    global last_record
    global stored_input_file

    input_file_name = param_input_file_name
    predicted_field_name = param_included_fields[0]

    maxInput = -sys.maxint - 1
    minInput = sys.maxint
    with open(input_file_name, "rb") as file_input:
        csv_reader = csv.reader(file_input)

        row = csv_reader.next()
        stored_input_file.append(row)
        index = 0
        for element in row:
            element = element.strip()
            if element == predicted_field_name:
                predicted_field_row = index
            else:
                index += 1

        row = csv_reader.next()
        stored_input_file.append(row)
        predicted_field_type = row[predicted_field_row].strip()
        row = csv_reader.next()
        stored_input_file.append(row)

        if predicted_field_type == "float":
            maxInput = (maxInput / 1.0)
            assert type(maxInput) is float
            minInput = (minInput / 1.0)
            assert type(minInput) is float

        for row in csv_reader:
            stored_input_file.append(row)
            if predicted_field_type == "int":
                original_input = int(row[predicted_field_row])
            else:
                original_input = float(row[predicted_field_row])

            if original_input > maxInput:
                maxInput = original_input

            if original_input < minInput:
                minInput = original_input

    max_value = maxInput
    min_value = minInput

    last_record = param_last_record

    SWARM_CONFIG["includedFields"][0]["fieldName"] = predicted_field_name
    SWARM_CONFIG["includedFields"][0]["fieldType"] = predicted_field_type
    SWARM_CONFIG["includedFields"][0]["maxValue"] = max_value
    SWARM_CONFIG["includedFields"][0]["minValue"] = min_value
    SWARM_CONFIG["streamDef"]["info"] = predicted_field_name
    SWARM_CONFIG["streamDef"]["streams"][0]["info"] = predicted_field_name
    SWARM_CONFIG["streamDef"]["streams"][0]["source"] = "file://" + input_file_name
    SWARM_CONFIG["streamDef"]["streams"][0]["last_record"] = last_record
    SWARM_CONFIG["inferenceArgs"]["predictedField"] = predicted_field_name

    if param_date_type != "OFF":
        global date_format
        if param_date_type == "US":
            date_format = date_format_US
        else:
            date_format = date_format_EU

        SWARM_CONFIG["includedFields"].append({"fieldName": stored_input_file[0][0], "fieldType": "datetime"})


    if len(param_included_fields) > 1:

        included_fields_index = 1
        while included_fields_index < len(param_included_fields):
            current_field_name = param_included_fields[included_fields_index]

            element_index = 0
            for element in stored_input_file[0]:
                element = element.strip()
                if element == current_field_name:
                    current_field_row = element_index
                else:
                    element_index += 1

            current_field_type = stored_input_file[1][current_field_row]
            current_field_max = -sys.maxint - 1
            current_field_min = sys.maxint

            current_field_index = 3
            while current_field_index < len(stored_input_file):

                current_field_value = float(stored_input_file[current_field_index][current_field_row])

                if current_field_value > current_field_max:
                    current_field_max = current_field_value

                if current_field_value < current_field_min:
                    current_field_min = current_field_value

                current_field_index += 1

            SWARM_CONFIG["includedFields"].append({"fieldName": current_field_name, "fieldType": current_field_type,
                                                   "maxValue": current_field_max, "minValue": current_field_min})

            included_fields_index += 1


def run_swarm(param_swarm):
    #print SWARM_CONFIG
    if param_swarm:
        permutations_runner.runWithConfig(SWARM_CONFIG, {'maxWorkers': 2, 'overwrite': True})


def get_model_parameters():
    from model_0.model_params import MODEL_PARAMS
    model_params = MODEL_PARAMS
    model_params["modelParams"]["spParams"]["maxBoost"] = 1.0
    return model_params

def run_experiment(param_output_file_name, param_included_fields):
    model_params = get_model_parameters()
    model = ModelFactory.create(model_params)
    model.enableInference({"predictedField": predicted_field_name})

    shifter = InferenceShifter()
    print "Storing results on", param_output_file_name
    with open(param_output_file_name, "w") as file_output:
        csv_writer = csv.writer(file_output)
        row = stored_input_file[0]
        outputRow = [row[0], row[predicted_field_row], "prediction", "anomaly score"]
        csv_writer.writerow(outputRow)

        input_file_index = 3
        counter = 0
        while input_file_index < len(stored_input_file):
            counter += 1
            if counter % 500 == 0:
                print "Read %i lines..." % counter

            row = stored_input_file[input_file_index]
            time_index = row[0]
            original_value = float(row[predicted_field_row])


            model_run_values = {}
            if date_format is not None:
                time_stamp = datetime.datetime.strptime(time_index, date_format)
                model_run_values.__setitem__(stored_input_file[0][0], time_stamp)

            param_index = 0
            while param_index < len(param_included_fields):
                current_param_name = param_included_fields[param_index]
                first_line_array = stored_input_file[0]
                current_param_row_index = first_line_array.index(current_param_name)
                model_run_values.__setitem__(current_param_name, float(row[current_param_row_index]))
                param_index += 1

            results = model.run(model_run_values)

            anomaly_score = results.inferences["anomalyScore"]
            shifted_result = shifter.shift(results)
            inference = shifted_result.inferences['multiStepBestPredictions'][1]

            if inference is None:
                inference = 0.00
            outputRow = [time_index, original_value, "%0.2f" % inference, anomaly_score]
            csv_writer.writerow(outputRow)

            input_file_index += 1


def after_processor(param_output_file_name):
    abs_difference_array = []
    with open(param_output_file_name, "rb") as file_output:
        csv_reader = csv.reader(file_output)
        csv_reader.next()
        csv_reader.next()
        for row in csv_reader:
            abs_difference_array.append(abs(float(row[1]) - float(row[2])))


    max_difference = max_value - min_value
    relative_difference_array = []
    total_relative_difference = 0
    index = 0

    # counter[0] = 0 - 0.9999
    # counter[1] = 1 - 25
    # counter[2] = 26 - 50
    # counter[3] = 51 - 75
    # counter[4] = 76 - 100
    # counter[5] = 100 - up
    counter = []
    counter.append(0)
    counter.append(0)
    counter.append(0)
    counter.append(0)
    counter.append(0)
    counter.append(0)
    while index < len(abs_difference_array):
        abs_difference_value = abs_difference_array[index]
        relative_difference_value = (abs_difference_value / float(max_difference)) * 100
        relative_difference_array.append(relative_difference_value)
        total_relative_difference += relative_difference_value
        index += 1

        if relative_difference_value < 1:
            counter[0] += 1
        elif relative_difference_value <= 25:
            counter[1] += 1
        elif relative_difference_value <= 50:
            counter[2] += 1
        elif relative_difference_value <= 75:
            counter[3] += 1
        elif relative_difference_value <= 100:
            counter[4] += 1
        else:
            counter[5] += 1

    index = 0
    while index < len(counter):
        counter[index] = (float(counter[index]) / len(abs_difference_array)) * 100
        index += 1

    print "Total relative difference: %0.2f" % total_relative_difference
    print "0 - 0.9  %0.2f%%" % counter[0]
    print "1 - 25   %0.2f%%" % counter[1]
    print "26 - 50  %0.2f%%" % counter[2]
    print "51 - 75  %0.2f%%" % counter[3]
    print "76 - 100 %0.2f%%" % counter[4]
    print "100+     %0.2f%%" % counter[5]

    output_note = param_output_file_name.replace(".csv", "")
    output_note += "_note.txt"
    with open(output_note, "w") as file_output_note:
        file_output_note.write("Total relative difference: %0.2f\n" % total_relative_difference)
        file_output_note.write("0 - 0.9  %0.2f%%\n" % counter[0])
        file_output_note.write("1 - 25   %0.2f%%\n" % counter[1])
        file_output_note.write("26 - 50  %0.2f%%\n" % counter[2])
        file_output_note.write("51 - 75  %0.2f%%\n" % counter[3])
        file_output_note.write("76 - 100 %0.2f%%\n" % counter[4])
        file_output_note.write("100+     %0.2f%%\n" % counter[5])

# input_file_name, output_file_name, last_record, date_type, predicted_field_name, other_included_field_name, etc...
# last_record = -1 if to not swarm, or last_record = x > 0 if to swarm
# date_type = OFF / US / EU (stands for Off, American, European)
if __name__ == "__main__":
    input_file_name = sys.argv[1]
    output_file_name = sys.argv[2]
    last_record = int(sys.argv[3])
    date_type = sys.argv[4]
    if last_record == -1:
        swarm = False
    else:
        swarm = True

    index = 5
    included_fields = []
    while index < len(sys.argv):
        included_fields.append(sys.argv[index])
        index += 1

    configure_swarm_parameters(input_file_name, last_record, date_type, included_fields)
    run_swarm(swarm)
    run_experiment(output_file_name, included_fields)
    after_processor(output_file_name)
