import csv


def read_csv(file_name):
    with open(f"/Users/cyang/PycharmProjects/LSMSimulator/src/data/synthetic_data/{file_name}") as file:
        csvreader = csv.reader(file)
        next(csvreader, None) # Skip header row
        rows = []
        for row in csvreader:
            rows.append(row)

    return rows

def write_to_csv(file_name, headers, rows):
    with open(f"/Users/cyang/PycharmProjects/LSMSimulator/src/data/synthetic_data/{file_name}", 'w') as file:
        csvwriter = csv.writer(file)
        csvwriter.writerow(headers)
        for row in rows:
            csvwriter.writerow(row)