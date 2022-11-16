import csv
from tkinter import Tk
from tkinter.filedialog import askopenfilename
from tkinter.filedialog import askdirectory
TK_SILENCE_DEPRECATION=1
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import time
import os

@dataclass
class textFile:
    path: str
    start_time: str = field(default_factory=str)
    sentence_times: list[str] = field(default_factory=list)
    sentence_absolute_times: list[str] = field(default_factory=list)
    sentences: list[str] = field(default_factory=list)


    def audio_start_time_from_path(self, csvInput) -> None:
        day = int(csvInput[0:2])
        month = int(csvInput[3:5])
        year = int(csvInput[6:10])
        hours = int(csvInput[11:13])
        minutes = int(csvInput[14:16])
        seconds = int(csvInput[17:19])
        combined = datetime(year, month, day, hours, minutes, seconds)
        return combined

    def getTimesAndSentences(self) -> None:
        with open(self.path, "r", encoding="utf-8-sig") as emotion_data:
            emotions_reader = csv.reader(emotion_data, delimiter=",")
            for x in emotions_reader:
                if (x[0] == "Start Time"):
                    self.start_time = self.audio_start_time_from_path(x[1])
                else:
                    self.sentence_times.append(x[0])
                    self.sentences.append(x[2])

    def convertElapsedTimesToAbsolute(self) -> None:
        for x in self.sentence_times:
            word_hours = float(x[0:2])
            word_minutes = float(x[3:5])
            word_seconds = float(x[6:8])
            plus_hours = timedelta(hours=word_hours)
            plus_minutes = timedelta(minutes=word_minutes)
            plus_seconds = timedelta(seconds=word_seconds)
            word_time = (self.start_time + plus_hours + plus_minutes + plus_seconds)
            time_appending = word_time.strftime('%H:%M:%S')
            self.sentence_absolute_times.append(time_appending)

    def findOverlappingIndexes(self, empatica_times) -> None:
        empatica_index_match = None
        sentence_index_match = None
        match_found = False
        for sentence_time, y in enumerate(self.sentence_absolute_times):
            for empatica_index, z in enumerate(empatica_times):
                if y == z:
                    sentence_index_match = sentence_time
                    empatica_index_match = empatica_index
                    match_found = True
                    break
            if match_found:
                break
        return sentence_index_match, empatica_index_match
    
    


@dataclass
class empatica:
    path_temp: str
    path_eda: str
    starting_time: str = ''
    start_time_unix: float = 0
    list_length: int = 0
    dividing_number: int = 0
    end_of_list: bool = False
    eda: list[float] = field(default_factory=list)
    temp: list[float] = field(default_factory=list)
    times: list[str] = field(default_factory=list)
    # Averaged from 4/sec to 1/sec
    eda_avg: list[float] = field(default_factory=list)
    temp_avg: list[float] = field(default_factory=list)

    def eda_extraction(self):
        eda_data = []
        skip_first = True
        with open(self.path_eda) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            counter = 0
            for row in csv_reader:
                if (counter == 0):
                    empatica_start_time = row[0]
                    empatica_start_time = float(empatica_start_time)
                    self.start_time_unix = empatica_start_time
                    timestamp = datetime.fromtimestamp(empatica_start_time)
                    converted_time = timestamp.strftime('%H:%M:%S')
                    self.starting_time = converted_time
                    #print(f"Converted start time = {converted_time}")
                    #greater than 1 because first data point is the time and second is the sampling rate then a 0 measurement
                if (counter > 2):
                    self.eda.append(float(row[0]))

                if counter == 1:
                    self.dividing_number = float(row[0])
                counter = counter + 1

    def temperature_extraction(self):
        counter = 0
        with open(self.path_temp) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in csv_reader:
                if (counter > 2):
                    self.temp.append(float(row[0]))
                counter = counter + 1

    def time_list_get(self):
        second = 1
        plus_time = timedelta(seconds=second)
        time_temp = datetime.fromtimestamp(self.start_time_unix)
        
        start_time_from_string = str(time_temp.strftime('%H:%M:%S'))

        date_time_starting = datetime.strptime(start_time_from_string, '%H:%M:%S')
        new_time = date_time_starting

        self.times.append(self.starting_time)
        skip_first = False
        for y in self.eda_avg:
            if skip_first:
                new_time = (new_time + plus_time)
                converted_new_time = new_time.strftime('%H:%M:%S')
                self.times.append(converted_new_time)
            skip_first = True
        self.list_length = len(self.times)

    def data_averager(self):
        counter = 0
        averager_temp = 0
        averager_eda = 0
        mini_counter = 0
        while (counter < len(self.temp) and counter < len(self.eda)):
            averager_temp = float(self.temp[counter]) + averager_temp
            averager_eda = float(self.eda[counter]) + averager_eda
            mini_counter = mini_counter + 1
            if (mini_counter == self.dividing_number):
                averager_temp = averager_temp / self.dividing_number
                averager_eda = averager_eda / self.dividing_number
                self.temp_avg.append(averager_temp)
                self.eda_avg.append(averager_eda)
                averager_temp = 0
                averager_eda = 0
                mini_counter = 0
            elif (counter == len(self.temp) - 1):
                averager_temp = averager_temp / mini_counter
                averager_eda = averager_eda / mini_counter
                self.temp_avg.append(averager_temp)
                self.eda_avg.append(averager_eda)
            counter = counter + 1

    def end_of_list_check(self, empatica_gps_match_index) -> None:
        if empatica_gps_match_index != None:
            if (empatica_gps_match_index + 1) == self.list_length:
                self.end_of_list = True


    def write_available_Empatica(self, csv_data, feature, empatica_gps_match_index) -> tuple[list, int]:

        csv_data.append(self.eda_avg[empatica_gps_match_index])
        csv_data.append(self.temp_avg[empatica_gps_match_index])
        

        feature.SetField("EDA (us)", self.eda_avg[empatica_gps_match_index])
        feature.SetField("Temp (C)", self.temp_avg[empatica_gps_match_index])


        empatica_gps_match_index += 1  
        
        return csv_data, feature, empatica_gps_match_index

    def no_empatica_to_save(self, csv_data) -> list:
        csv_data.append("N/A")
        csv_data.append("N/A")
        return csv_data

    

print("Please select the text file with the sentences now:")

txt_file_path = askopenfilename()
textFileData = textFile(path=txt_file_path)
textFileData.getTimesAndSentences()
# Testing things
print(textFileData.start_time)
print(textFileData.sentence_times)
print(textFileData.sentences)

textFileData.convertElapsedTimesToAbsolute()
print(textFileData.sentence_absolute_times)

# inputs from the empatica
print("Now select the empatica eda file")
eda_path = askopenfilename()
print("Now select the empatica temp file")
temp_path = askopenfilename()

# making the data class for all of the relevant empatica data
Empatica = empatica(path_temp=temp_path, path_eda=eda_path)
Empatica.eda_extraction()
Empatica.temperature_extraction()
Empatica.data_averager()
Empatica.time_list_get()

# Now finding the index for the first sentence spoken that overlaps with the eda data
# The audio will always start first so the senteceindex match will be the starting poing for the overlaps
sentence_index_match, empatica_index_match = textFileData.findOverlappingIndexes(Empatica.times)
print(f"sentence index is: {sentence_index_match}\nempatica index match is: {empatica_index_match}\n")

print("where do you want to save this file?: ")
saveFilePath = askdirectory(title="Select the folder you wish to save the ouput file in")
print(f"\n\nSave file path: {saveFilePath}\n\n")
print("What would you like to name this file?: ")
fileNameInput = input()

data_writer = open(saveFilePath +  fileNameInput + '.csv', 'w', newline='')
writer = csv.writer(data_writer)
csv_titles = ['time', 'eda vals', 'temp vals', 'sentences']
writer.writerow(csv_titles)

def creatingNewCSV():
    for empaticaIdx, e_time in enumerate  in Empatica.times:
        row_to_write = []

        row_to_write.append(e_time, Empatica.eda_avg[empaticaIdx], Empatica.temp_avg[empaticaIdx])

        # this is all so far, wont need much else code really
        





