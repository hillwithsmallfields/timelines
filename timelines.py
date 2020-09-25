#!/usr/bin/python3

import argparse
import csv
import datetime
import os.path

PREFER_LEFTMOST = True          # if false, tries to re-use the column last occupied furthest back (doesn't work yet)

this_year = datetime.date.today().year

class Interval():

    def __init__(self, begin, end, subject, area):
        self.begin = begin
        self.end = end
        self.subject = subject
        self.area = area

    def __str__(self):
        return "<from %d to %d: %s (%s)>" % (self.begin, self.end, self.subject, self.area)
        
class TimeLines():

    def __init__(self):
        self.columns = []

    def add_data(self, rowsource):
        for row in rowsource:
            self.add_row(row)

    def add_row(self, row):
        if row['Begin date'] == "":
            return
        begin = int(row['Begin date'])
        raw_end = row['End date']
        end = (this_year
               if raw_end == '*'
               else (begin
                     if (raw_end == '.' or raw_end == "")
                     else int(raw_end)))
        interval = Interval(begin, end,
                            row['Subject'], row['Area'])
        if not self.columns:
            self.columns.append([interval])
            return
        earliest_end = self.columns[0][-1].end
        best_column = None
        for colno, coldata in enumerate(self.columns):
            latest = coldata[-1].end
            if latest < begin and PREFER_LEFTMOST or end < earliest_end:
                best_column = colno
                earliest_end = end
        if best_column:
            self.columns[best_column].append(interval)
        else:
            self.columns.append([interval])

    def dump_raw(self):
        for colno, coldata in enumerate(self.columns):
            print("column", colno)
            for interval in coldata:
                print("  ", interval)

    def fill_in_gaps(self):
        """Put filler intervals in the gaps in each column."""
        earliest_year = this_year
        for column in self.columns:
            if column[0].begin < earliest_year:
                earliest_year = column[0].begin
        for column in self.columns:
            gap_start = earliest_year
            # first filler is from earliest time to start of this column
            # last filler is from end of this column until now
            pass

    def output_HTML(self, filename):
        with open(filename, 'w') as outstream:
            pass                # TODO: write this
    
    def output_SVG(self, filename):
        with open(filename, 'w') as outstream:
            pass                # TODO: write this
    
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", nargs="+",
                        help="""Input files (CSV)""")
    parser.add_argument("-o", "--output",
                        help="""Output file""")
    args = parser.parse_args()

    timelines = TimeLines()

    for filename in args.input:
        with open(filename) as instream:
            reader = csv.DictReader(instream)
            timelines.add_data(reader)

    timelines.dump_raw()

    output = args.output or os.path.splitext(args.input[0])[0] + ".html"
    
    if output.endswith(".html"):
        timelines.fill_in_gaps()
        timelines.output_HTML(output)
    elif output.endswith(".svg"):
        timelines.output_SVG(output)
    else:
        print("I don't know how to write that kind of output.")

if __name__ == "__main__":
    main()
    
